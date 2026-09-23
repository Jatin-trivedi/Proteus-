//go:build !windows

package main

import (
	"os"
	"strconv"
	"strings"
)

// getUptimeMinutes returns system uptime in minutes on Linux/macOS.
//
// Linux: reads /proc/uptime  (first field = seconds since boot, float)
// macOS: /proc/uptime does not exist → returns 0 (check is skipped)
//
// This file is compiled on every non-Windows platform, which includes
// the Ubuntu CI runner in GitHub Actions.  It keeps `go build GOOS=linux`
// working without importing the windows package.
func getUptimeMinutes() int {
	data, err := os.ReadFile("/proc/uptime")
	if err != nil {
		// macOS or unreadable — skip the uptime check
		return 0
	}

	// /proc/uptime format: "12345.67 98765.43\n"
	// First field = total uptime seconds (float), second = idle time.
	fields := strings.Fields(string(data))
	if len(fields) == 0 {
		return 0
	}

	seconds, err := strconv.ParseFloat(fields[0], 64)
	if err != nil {
		return 0
	}

	return int(seconds / 60)
}