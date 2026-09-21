package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"time"
)

type IROperation struct {
	ID         string         `json:"id"`
	Type       string         `json:"type"`
	Parameters map[string]any `json:"parameters"`
}

type IRDocument struct {
	Version      string        `json:"version"`
	IRType       string        `json:"ir_type"`
	Investigation string       `json:"investigation"`
	Operations   []IROperation `json:"operations"`
}

type OperationResult struct {
	OperationID string         `json:"operation_id"`
	Type        string         `json:"type"`
	Status      string         `json:"status"`
	Data        map[string]any `json:"data,omitempty"`
	Error       map[string]string `json:"error,omitempty"`
	DurationMS  float64        `json:"duration_ms,omitempty"`
}

type ExecutionResult struct {
	Investigation string          `json:"investigation"`
	Version       string          `json:"version"`
	Results       []OperationResult `json:"results"`
}

type irHandler func(context.Context, IROperation) (map[string]any, error)

func ParseIRDocumentJSON(raw string) (IRDocument, error) {
	var doc IRDocument
	if err := json.Unmarshal([]byte(raw), &doc); err != nil {
		return IRDocument{}, err
	}
	if doc.Version == "" {
		return IRDocument{}, fmt.Errorf("IRDocument version is required")
	}
	if doc.IRType == "" {
		return IRDocument{}, fmt.Errorf("IRDocument ir_type is required")
	}
	if doc.Investigation == "" {
		return IRDocument{}, fmt.Errorf("IRDocument investigation is required")
	}
	return doc, nil
}

func executeIRDocument(doc IRDocument) (ExecutionResult, error) {
	if doc.Version == "" {
		return ExecutionResult{}, fmt.Errorf("missing IR document version")
	}

	result := ExecutionResult{
		Investigation: doc.Investigation,
		Version:       doc.Version,
		Results:       make([]OperationResult, 0, len(doc.Operations)),
	}

	for _, op := range doc.Operations {
		start := time.Now()
		item := OperationResult{
			OperationID: op.ID,
			Type:        op.Type,
			Status:      "success",
		}

		data, err := dispatchIROperation(context.Background(), op)
		if err != nil {
			item.Status = "error"
			item.Error = map[string]string{"message": err.Error()}
			item.DurationMS = float64(time.Since(start).Milliseconds())
			result.Results = append(result.Results, item)
			continue
		}
		item.Data = data
		item.DurationMS = float64(time.Since(start).Milliseconds())
		result.Results = append(result.Results, item)
	}
	return result, nil
}

func executeIRDocumentJSON(raw string) (ExecutionResult, error) {
	doc, err := ParseIRDocumentJSON(raw)
	if err != nil {
		return ExecutionResult{}, err
	}
	return executeIRDocument(doc)
}

func dispatchIROperation(ctx context.Context, op IROperation) (map[string]any, error) {
	handlers := map[string]irHandler{
		"system.info":        handleSystemInfo,
		"system.users":       handleSystemUsers,
		"processes.list":     handleProcessesList,
		"processes.details":  handleProcessesDetails,
		"network.interfaces": handleNetworkInterfaces,
		"network.connections": handleNetworkConnections,
		"network.routes":     handleNetworkRoutes,
		"network.dns":        handleNetworkDNS,
		"filesystem.metadata": handleFilesystemMetadata,
		"filesystem.hash":    handleFilesystemHash,
	}
	if handler, ok := handlers[op.Type]; ok {
		return handler(ctx, op)
	}
	return nil, fmt.Errorf("unsupported operation type: %s", op.Type)
}

func getParamString(params map[string]any, key string, fallback string) string {
	if params == nil {
		return fallback
	}
	if value, ok := params[key]; ok {
		switch v := value.(type) {
		case string:
			if strings.TrimSpace(v) != "" {
				return v
			}
		case fmt.Stringer:
			return v.String()
		default:
			if s, err := json.Marshal(v); err == nil {
				return string(s)
			}
		}
	}
	return fallback
}

func getParamBool(params map[string]any, key string, fallback bool) bool {
	if params == nil {
		return fallback
	}
	if value, ok := params[key]; ok {
		switch v := value.(type) {
		case bool:
			return v
		case string:
			return strings.EqualFold(v, "true") || strings.EqualFold(v, "1") || strings.EqualFold(v, "yes")
		case float64:
			return v != 0
		case int:
			return v != 0
		}
	}
	return fallback
}

func handleSystemInfo(_ context.Context, _ IROperation) (map[string]any, error) {
	host, _ := os.Hostname()
	username := os.Getenv("USERNAME")
	if username == "" {
		username = os.Getenv("USER")
	}
	if u, err := user.Current(); err == nil && u != nil {
		username = u.Username
	}
	return map[string]any{
		"hostname": host,
		"username": username,
		"os":       runtime.GOOS,
		"arch":     runtime.GOARCH,
		"elevated": IsElevated(),
	}, nil
}

func handleSystemUsers(_ context.Context, _ IROperation) (map[string]any, error) {
	users := []map[string]any{}
	if current, err := user.Current(); err == nil && current != nil {
		users = append(users, map[string]any{"username": current.Username, "uid": current.Uid, "gid": current.Gid})
	}
	if username := os.Getenv("USERNAME"); username != "" {
		users = append(users, map[string]any{"username": username, "uid": "env", "gid": "env"})
	}
	seen := map[string]bool{}
	filtered := make([]map[string]any, 0, len(users))
	for _, entry := range users {
		key := fmt.Sprintf("%v", entry["username"])
		if seen[key] {
			continue
		}
		seen[key] = true
		filtered = append(filtered, entry)
	}
	return map[string]any{"users": filtered}, nil
}

func handleProcessesList(_ context.Context, _ IROperation) (map[string]any, error) {
	items, err := listProcessesSnapshot()
	if err != nil {
		return nil, err
	}
	return map[string]any{"processes": items}, nil
}

func handleProcessesDetails(_ context.Context, op IROperation) (map[string]any, error) {
	pid := getParamString(op.Parameters, "pid", "")
	if pid == "" {
		items, err := listProcessesSnapshot()
		if err != nil {
			return nil, err
		}
		if len(items) == 0 {
			return map[string]any{"processes": []map[string]any{}}, nil
		}
		return map[string]any{"processes": items[:min(5, len(items))]}, nil
	}
	return map[string]any{"pid": pid, "name": filepath.Base(pid)}, nil
}

func handleNetworkInterfaces(_ context.Context, _ IROperation) (map[string]any, error) {
	ifs, err := net.Interfaces()
	if err != nil {
		return nil, err
	}
	result := make([]map[string]any, 0, len(ifs))
	for _, iface := range ifs {
		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}
		ips := make([]string, 0, len(addrs))
		for _, addr := range addrs {
			ips = append(ips, addr.String())
		}
		result = append(result, map[string]any{
			"name":        iface.Name,
			"hardware_id": iface.HardwareAddr.String(),
			"flags":       iface.Flags.String(),
			"addresses":   ips,
		})
	}
	return map[string]any{"interfaces": result}, nil
}

func handleNetworkConnections(_ context.Context, _ IROperation) (map[string]any, error) {
	cmd := "netstat -ano"
	if runtime.GOOS != "windows" {
		cmd = "ss -tunap || netstat -an"
	}
	output, err := runCommand(cmd)
	if err != nil {
		return nil, err
	}
	return map[string]any{"connections": splitLines(output)}, nil
}

func handleNetworkRoutes(_ context.Context, _ IROperation) (map[string]any, error) {
	cmd := "route print"
	if runtime.GOOS != "windows" {
		cmd = "ip route || route -n"
	}
	output, err := runCommand(cmd)
	if err != nil {
		return nil, err
	}
	return map[string]any{"routes": splitLines(output)}, nil
}

func handleNetworkDNS(_ context.Context, op IROperation) (map[string]any, error) {
	target := getParamString(op.Parameters, "domain", "localhost")
	if target == "" {
		target = "localhost"
	}
	addrs, err := net.LookupIP(target)
	if err != nil {
		return map[string]any{"domain": target, "addresses": []string{}}, nil
	}
	out := make([]string, 0, len(addrs))
	for _, ip := range addrs {
		out = append(out, ip.String())
	}
	sort.Strings(out)
	return map[string]any{"domain": target, "addresses": out}, nil
}

func handleFilesystemMetadata(_ context.Context, op IROperation) (map[string]any, error) {
	path := getParamString(op.Parameters, "path", ".")
	info, err := os.Stat(path)
	if err != nil {
		return nil, err
	}
	return map[string]any{
		"path":         path,
		"exists":       true,
		"is_dir":       info.IsDir(),
		"size":         info.Size(),
		"mode":         info.Mode().String(),
		"modified_at":  info.ModTime().UTC().Format(time.RFC3339),
		"name":         info.Name(),
	}, nil
}

func handleFilesystemHash(_ context.Context, op IROperation) (map[string]any, error) {
	path := getParamString(op.Parameters, "path", os.Args[0])
	if path == "" {
		path = os.Args[0]
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	sum := sha256.Sum256(data)
	return map[string]any{
		"path":   path,
		"sha256": hex.EncodeToString(sum[:]),
		"size":   len(data),
	}, nil
}

func listProcessesSnapshot() ([]map[string]any, error) {
	cmd := "tasklist /FO CSV /NH"
	if runtime.GOOS != "windows" {
		cmd = "ps -eo pid,comm --no-headers"
	}
	output, err := runCommand(cmd)
	if err != nil {
		return nil, err
	}
	lines := splitLines(output)
	items := make([]map[string]any, 0, len(lines))
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}
		parts := strings.SplitN(line, " ", 2)
		if len(parts) == 2 {
			items = append(items, map[string]any{"pid": parts[0], "name": strings.TrimSpace(parts[1])})
			continue
		}
		items = append(items, map[string]any{"name": strings.TrimSpace(line)})
	}
	return items, nil
}

func runCommand(cmd string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 12*time.Second)
	defer cancel()
	parts := strings.Fields(cmd)
	if len(parts) == 0 {
		return "", fmt.Errorf("empty command")
	}
	command := exec.CommandContext(ctx, parts[0], parts[1:]...)
	output, err := command.CombinedOutput()
	if err != nil {
		return string(output), err
	}
	return string(output), nil
}

func splitLines(raw string) []string {
	lines := strings.Split(strings.ReplaceAll(strings.ReplaceAll(raw, "\r\n", "\n"), "\r", "\n"), "\n")
	out := make([]string, 0, len(lines))
	for _, line := range lines {
		if strings.TrimSpace(line) != "" {
			out = append(out, strings.TrimSpace(line))
		}
	}
	return out
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
