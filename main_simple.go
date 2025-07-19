package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"sync"
	"time"

	"github.com/creack/pty"
	"github.com/gliderlabs/ssh"
)

// ChatMessage represents a chat message
type ChatMessage struct {
	Username  string    `json:"username"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
}

// SessionManager manages active SSH sessions and chat
type SessionManager struct {
	sessions map[string]*Session
	mutex    sync.RWMutex
}

// Session represents an active SSH session
type Session struct {
	ID       string
	Username string
	SSH      ssh.Session
	PTY      *os.File
}

var sessionManager = &SessionManager{
	sessions: make(map[string]*Session),
}

// AddSession adds a new session to the manager
func (sm *SessionManager) AddSession(id, username string, sshSession ssh.Session, ptyFile *os.File) {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	sm.sessions[id] = &Session{
		ID:       id,
		Username: username,
		SSH:      sshSession,
		PTY:      ptyFile,
	}
	log.Printf("Added session %s for user %s. Total sessions: %d", id, username, len(sm.sessions))
}

// RemoveSession removes a session from the manager
func (sm *SessionManager) RemoveSession(id string) {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	if session, exists := sm.sessions[id]; exists {
		log.Printf("Removing session %s for user %s", id, session.Username)
		delete(sm.sessions, id)
	}
}

// BroadcastMessage sends a chat message to all active sessions
func (sm *SessionManager) BroadcastMessage(msg ChatMessage) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	log.Printf("Broadcasting message from %s: %s", msg.Username, msg.Message)
	
	// Write to chat file for all sessions to read
	chatFile := "/tmp/ssh-chat.log"
	file, err := os.OpenFile(chatFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err == nil {
		messageData, _ := json.Marshal(msg)
		file.WriteString(string(messageData) + "\n")
		file.Close()
	}
}

// GetActiveUsers returns a list of active usernames
func (sm *SessionManager) GetActiveUsers() []string {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	users := make([]string, 0, len(sm.sessions))
	for _, session := range sm.sessions {
		users = append(users, session.Username)
	}
	return users
}

func main() {
	// Clean up chat file on start
	os.Remove("/tmp/ssh-chat.log")
	
	ssh.Handle(func(s ssh.Session) {
		// Generate a unique session ID
		sessionID := fmt.Sprintf("session-%d", time.Now().UnixNano())
		
		// Use remote address as username if no user provided
		username := s.User()
		if username == "" {
			username = fmt.Sprintf("User-%s", s.RemoteAddr().String())
		}

		// Check if a PTY was requested
		ptyReq, winCh, isPty := s.Pty()
		if !isPty {
			io.WriteString(s, "No PTY requested.\n")
			s.Exit(1)
			return
		}

		// Start the command with a PTY
		cmd := exec.Command("./.venv/bin/python3", "main.py")
		
		// Set environment variables for the Python app
		cmd.Env = append(os.Environ(),
			fmt.Sprintf("SSH_SESSION_ID=%s", sessionID),
			fmt.Sprintf("SSH_USERNAME=%s", username),
		)

		// Start the PTY
		ptmx, err := pty.StartWithSize(cmd, &pty.Winsize{
			Rows: uint16(ptyReq.Window.Height),
			Cols: uint16(ptyReq.Window.Width),
		})
		if err != nil {
			io.WriteString(s, "Error starting PTY: "+err.Error()+"\n")
			return
		}
		
		// Add session to manager
		sessionManager.AddSession(sessionID, username, s, ptmx)
		
		defer func() {
			sessionManager.RemoveSession(sessionID)
			_ = ptmx.Close()
			_ = cmd.Process.Kill()
		}()

		// Handle window resize
		go func() {
			for win := range winCh {
				_ = pty.Setsize(ptmx, &pty.Winsize{
					Rows: uint16(win.Height),
					Cols: uint16(win.Width),
				})
			}
		}()

		// Monitor for special chat commands from the Python app
		go func() {
			buffer := make([]byte, 4096)
			var accumulated string
			
			for {
				n, err := ptmx.Read(buffer)
				if err != nil {
					return
				}
				
				data := string(buffer[:n])
				accumulated += data
				
				// Process complete lines
				for {
					lineEnd := -1
					for i, c := range accumulated {
						if c == '\n' || c == '\r' {
							lineEnd = i
							break
						}
					}
					
					if lineEnd == -1 {
						break // No complete line yet
					}
					
					line := accumulated[:lineEnd]
					accumulated = accumulated[lineEnd+1:]
					
					// Check if this is a chat message
					if len(line) > 5 && line[:5] == "CHAT:" {
						var chatMsg ChatMessage
						chatData := line[5:]
						if err := json.Unmarshal([]byte(chatData), &chatMsg); err == nil {
							chatMsg.Username = username
							chatMsg.Timestamp = time.Now()
							sessionManager.BroadcastMessage(chatMsg)
						}
						continue // Don't send chat commands to client
					}
					
					// Regular output, send to client
					s.Write([]byte(line + "\n"))
				}
				
				// Send any remaining non-line data
				if len(accumulated) > 0 && len(accumulated) < 100 {
					// Only send if it's not too much accumulated data
					hasNewline := false
					for _, c := range accumulated {
						if c == '\n' || c == '\r' {
							hasNewline = true
							break
						}
					}
					if !hasNewline {
						s.Write([]byte(accumulated))
						accumulated = ""
					}
				}
			}
		}()

		// Copy session input to PTY
		_, _ = io.Copy(ptmx, s)
	})

	log.Println("Listening on port 2223...")
	log.Fatal(ssh.ListenAndServe(":2223", nil))
}
