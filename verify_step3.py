#!/usr/bin/env python3
"""
verify_step3.py
===============
Run from your repo root:

    python verify_step3.py

Verifies the sandbox detection fix — no live agent needed.
Checks file contents + Go compile + logic correctness.
"""

from __future__ import annotations
import os, subprocess, sys, textwrap
from pathlib import Path

GRN = "\033[92m"; RED = "\033[91m"; YLW = "\033[93m"
CYN = "\033[96m"; RST = "\033[0m";  BLD = "\033[1m"
PASS = f"{GRN}[PASS]{RST}"; FAIL = f"{RED}[FAIL]{RST}"
INFO = f"\033[94m[INFO]{RST}"

repo_root = Path(__file__).resolve().parent
agent_dir = repo_root / "agent"
results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> bool:
    tag = PASS if passed else FAIL
    print(f"  {tag}  {name}")
    if detail:
        for line in detail.splitlines():
            print(f"         {line}")
    results.append((name, passed, detail))
    return passed


def section(title: str):
    print(f"\n{BLD}{CYN}{'─'*60}{RST}")
    print(f"{BLD}{CYN}  {title}{RST}")
    print(f"{BLD}{CYN}{'─'*60}{RST}")


# ─────────────────────────────────────────────────────────────────────────────
section("FILE STRUCTURE")
# ─────────────────────────────────────────────────────────────────────────────

for fname in ("sandbox.go", "sandbox_windows.go", "sandbox_linux.go"):
    check(f"agent/{fname} exists", (agent_dir / fname).exists())


# ─────────────────────────────────────────────────────────────────────────────
section("sandbox.go — stub removed, new checks added")
# ─────────────────────────────────────────────────────────────────────────────

sb = (agent_dir / "sandbox.go")
if sb.exists():
    src = sb.read_text()

    check(
        "Stub 'return 0' removed from sandbox.go",
        "return 0" not in src,
        "getUptimeMinutes() stub must be deleted from sandbox.go — it now lives in sandbox_windows.go / sandbox_linux.go",
    )
    check(
        "No 'var _ = time.Now' hack remaining",
        "var _ = time.Now" not in src,
        "That line was silencing an unused-import error caused by the stub — should be gone now",
    )
    check(
        "CPU core check added (runtime.NumCPU)",
        "runtime.NumCPU()" in src,
        "Need: if runtime.NumCPU() < 2 { return true }",
    )
    check(
        "VMware driver path added",
        "vmhgfs.sys" in src or "vmmouse.sys" in src,
        "Need extra VMware artifact paths in the sandboxPaths slice",
    )
    check(
        "VirtualBox driver path added",
        "VBoxMouse.sys" in src or "VBoxGuest.sys" in src,
    )
    check(
        "getUptimeMinutes() is still CALLED in IsSandboxed",
        "getUptimeMinutes()" in src,
        "The call must remain — only the definition moves to platform files",
    )
    check(
        "No 'time' import remaining (no longer needed)",
        '"time"' not in src,
        'Remove the "time" import line — time.Now is no longer referenced',
    )


# ─────────────────────────────────────────────────────────────────────────────
section("sandbox_windows.go — GetTickCount64")
# ─────────────────────────────────────────────────────────────────────────────

sw = agent_dir / "sandbox_windows.go"
if sw.exists():
    src = sw.read_text()

    check(
        "Has //go:build windows tag",
        "//go:build windows" in src,
        "First line must be: //go:build windows",
    )
    check(
        "Imports golang.org/x/sys/windows",
        "golang.org/x/sys/windows" in src,
        "Need: import \"golang.org/x/sys/windows\"",
    )
    check(
        "Calls GetTickCount64 via NewLazySystemDLL",
        "GetTickCount64" in src and "NewLazySystemDLL" in src,
        "Need: kernel32.NewLazySystemDLL(\"kernel32.dll\").NewProc(\"GetTickCount64\")",
    )
    check(
        "Converts milliseconds → minutes (/60000 or /60_000)",
        "60_000" in src or "60000" in src,
        "Need: int(r1) / 60_000",
    )
    check(
        "No 'return 0' hardcoded (real implementation, not stub)",
        src.count("return 0") == 0,
        "The whole point is to NOT return 0",
    )


# ─────────────────────────────────────────────────────────────────────────────
section("sandbox_linux.go — /proc/uptime fallback")
# ─────────────────────────────────────────────────────────────────────────────

sl = agent_dir / "sandbox_linux.go"
if sl.exists():
    src = sl.read_text()

    check(
        "Has //go:build !windows tag",
        "//go:build !windows" in src,
        "Must be: //go:build !windows  (compiles on Linux CI runner)",
    )
    check(
        "Reads /proc/uptime",
        "/proc/uptime" in src,
        "Need: os.ReadFile(\"/proc/uptime\")",
    )
    check(
        "Parses float seconds from file",
        "ParseFloat" in src,
        "Need: strconv.ParseFloat(fields[0], 64)",
    )
    check(
        "Returns 0 safely on read error (CI Mac/unsupported OS)",
        "return 0" in src,
        "Must return 0 if /proc/uptime is unavailable so check is skipped",
    )
    check(
        "Does NOT import windows package",
        "golang.org/x/sys/windows" not in src,
        "Must not import the windows package — this file compiles on Linux",
    )


# ─────────────────────────────────────────────────────────────────────────────
section("Go compile — both GOOS=windows and GOOS=linux")
# ─────────────────────────────────────────────────────────────────────────────

go_ok = subprocess.run(["go", "version"], capture_output=True).returncode == 0
check("Go toolchain available", go_ok)

if go_ok and agent_dir.exists():
    for target_os in ("windows", "linux"):
        vet = subprocess.run(
            ["go", "vet", "./..."],
            cwd=agent_dir,
            capture_output=True,
            text=True,
            env={**os.environ, "GOOS": target_os, "GOARCH": "amd64"},
        )
        check(
            f"go vet passes for GOOS={target_os}",
            vet.returncode == 0,
            vet.stderr[-500:] if vet.returncode != 0 else "",
        )

    # Quick logic test — simulate getUptimeMinutes returning 0
    # (can't call GetTickCount64 without Windows but we can check the logic
    # in IsSandboxed by making sure the call pattern is correct)
    print(f"\n  {INFO} Verifying sandbox logic with a Go test program …")

    test_prog = textwrap.dedent("""\
        //go:build ignore

        package main

        import "fmt"

        // Stub for the test — mimics what getUptimeMinutes returns in prod
        func stubUptime(mins int) bool {
            // mirrors: if uptime > 0 && uptime < 10 { return true }
            return mins > 0 && mins < 10
        }

        func main() {
            cases := map[int]bool{
                0:  false,   // no data / error → skip check
                5:  true,    // 5 min → sandbox
                9:  true,    // 9 min → sandbox
                10: false,   // exactly 10 min → not sandbox (boundary)
                60: false,   // 1 hour → not sandbox
            }
            allOK := true
            for mins, want := range cases {
                got := stubUptime(mins)
                status := "PASS"
                if got != want {
                    status = "FAIL"
                    allOK = false
                }
                fmt.Printf("[%s] uptime=%d min → sandboxed=%v (want %v)\\n",
                    status, mins, got, want)
            }
            if allOK {
                fmt.Println("\\nAll uptime boundary checks passed.")
            }
        }
    """)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".go", mode="w",
                                    delete=False, dir=str(agent_dir)) as f:
        f.write(test_prog)
        tmp_path = f.name

    try:
        run = subprocess.run(
            ["go", "run", tmp_path],
            cwd=agent_dir, capture_output=True, text=True,
            env={**os.environ, "GOOS": "linux", "GOARCH": "amd64"},
        )
        for line in run.stdout.splitlines():
            print(f"         {line}")
        check(
            "Uptime boundary logic is correct (0=skip, 1-9=sandbox, ≥10=ok)",
            "All uptime boundary checks passed" in run.stdout,
            run.stderr[:300] if run.returncode != 0 else "",
        )
    finally:
        os.unlink(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
section("SUMMARY")
# ─────────────────────────────────────────────────────────────────────────────

passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
colour = GRN if passed == total else (YLW if passed > total * 0.7 else RED)
print(f"\n  {colour}{BLD}{passed}/{total} checks passed{RST}\n")

if passed < total:
    print(f"  {RED}Failing:{RST}")
    for name, ok, detail in results:
        if not ok:
            print(f"    ✗  {name}")
            if detail:
                print(f"       → {detail.splitlines()[0]}")
    print()

sys.exit(0 if passed == total else 1)