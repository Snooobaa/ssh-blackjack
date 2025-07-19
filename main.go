package main

import (
	"io"
	"log"
	"os/exec"

	"github.com/creack/pty"
	"github.com/gliderlabs/ssh"
)

func main() {
	ssh.Handle(func(s ssh.Session) {
		// Check if a PTY was requested
		ptyReq, winCh, isPty := s.Pty()
		if !isPty {
			io.WriteString(s, "No PTY requested.\n")
			s.Exit(1)
			return
		}

		// Start the command with a PTY
		cmd := exec.Command("./.venv/bin/python3", "main.py")

		// Start the PTY
		ptmx, err := pty.StartWithSize(cmd, &pty.Winsize{
			Rows: uint16(ptyReq.Window.Height),
			Cols: uint16(ptyReq.Window.Width),
		})
		if err != nil {
			io.WriteString(s, "Error starting PTY: "+err.Error()+"\n")
			return
		}
		defer func() {
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

		// Copy data
		go io.Copy(ptmx, s)
		_, _ = io.Copy(s, ptmx)
	})

	log.Println("Listening on port 2222...")
	log.Fatal(ssh.ListenAndServe(":2222", nil))
}
