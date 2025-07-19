package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"

	"github.com/creack/pty"
	"github.com/gliderlabs/ssh"
	"github.com/fsnotify/fsnotify"
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
	if err != nil {
		log.Printf("Error opening chat file: %v", err)
		return
	}
	defer file.Close()
	
	messageData, err := json.Marshal(msg)
	if err != nil {
		log.Printf("Error marshaling chat message: %v", err)
		return
	}
	
	_, err = file.WriteString(string(messageData) + "\n")
	if err != nil {
		log.Printf("Error writing to chat file: %v", err)
		return
	}
	
	log.Printf("Successfully wrote chat message to file: %s", string(messageData))
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

// watchChatMessages monitors the chat messages file for new messages
func watchChatMessages() {
	chatFile := "/tmp/ssh-chat-messages.log"
	
	// Create watcher
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Printf("Failed to create file watcher: %v", err)
		return
	}
	defer watcher.Close()

	// Add the chat file directory to watcher
	err = watcher.Add(filepath.Dir(chatFile))
	if err != nil {
		log.Printf("Failed to watch directory: %v", err)
		return
	}

	var lastPos int64 = 0
	
	for {
		select {
		case event, ok := <-watcher.Events:
			if !ok {
				return
			}
			
			// Check if our chat file was modified
			if event.Name == chatFile && event.Op&fsnotify.Write == fsnotify.Write {
				log.Printf("Detected change in chat messages file")
				
				// Open and read file from last position
				file, err := os.Open(chatFile)
				if err != nil {
					log.Printf("Failed to open chat file: %v", err)
					continue
				}
				
				// Seek to last position
				_, err = file.Seek(lastPos, 0)
				if err != nil {
					log.Printf("Failed to seek in chat file: %v", err)
					file.Close()
					continue
				}
				
				// Read new lines
				scanner := bufio.NewScanner(file)
				for scanner.Scan() {
					line := scanner.Text()
					if line != "" {
						log.Printf("Processing chat message from file: %s", line)
						
						var chatMsg ChatMessage
						if err := json.Unmarshal([]byte(line), &chatMsg); err == nil {
							// Don't override the timestamp from the file, use the provided one
							sessionManager.BroadcastMessage(chatMsg)
							log.Printf("Successfully broadcasted file-based chat message from %s", chatMsg.Username)
						} else {
							log.Printf("Failed to parse chat message from file: %v", err)
						}
					}
				}
				
				// Update position
				pos, _ := file.Seek(0, 1)
				lastPos = pos
				file.Close()
			}
			
		case err, ok := <-watcher.Errors:
			if !ok {
				return
			}
			log.Printf("File watcher error: %v", err)
		}
	}
}

func main() {
	// Clean up chat files on start
	os.Remove("/tmp/ssh-chat.log")
	os.Remove("/tmp/ssh-chat-messages.log")
	
	// Start file watcher for chat messages
	go watchChatMessages()
	
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

		// Monitor PTY output and forward to SSH client (simplified - no chat parsing)
		go func() {
			buffer := make([]byte, 4096)
			
			for {
				n, err := ptmx.Read(buffer)
				if err != nil {
					log.Printf("PTY read error for session %s: %v", sessionID, err)
					return
				}
				
				// Simply forward all PTY output to the SSH client
				data := buffer[:n]
				s.Write(data)
			}
		}()

		// Copy session input to PTY
		_, _ = io.Copy(ptmx, s)
	})

	port := os.Getenv("SSH_PORT")
	if port == "" {
		port = "22" // default port
	}
	
	log.Printf("Listening on port %s...", port)
	log.Fatal(ssh.ListenAndServe(":"+port, nil))
}
