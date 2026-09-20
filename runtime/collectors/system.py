"""
Proteus JOCKY Forensic Runtime - System Collectors
Implements:
- system.info()
- system.users()
"""

import os
import sys
import socket
import platform
import getpass
import time
import re
from typing import Dict, Any, List

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode


def _get_uptime_string() -> str:
    """Calculates system uptime in a cross-platform and graceful manner."""
    # 1. Windows: kernel32.GetTickCount64
    if platform.system() == "Windows":
        try:
            import ctypes
            msec = ctypes.windll.kernel32.GetTickCount64()
            sec = int(msec / 1000)
            return f"{sec}s"
        except Exception:
            pass

    # 2. Linux: /proc/uptime
    if os.path.exists("/proc/uptime"):
        try:
            with open("/proc/uptime", "r") as f:
                sec = int(float(f.read().split()[0]))
                return f"{sec}s"
        except Exception:
            pass

    # 3. macOS / BSD: sysctl kern.boottime
    if platform.system() in ("Darwin", "FreeBSD", "OpenBSD"):
        try:
            import subprocess
            out = subprocess.check_output(
                ["sysctl", "-n", "kern.boottime"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            m = re.search(r"sec\s*=\s*(\d+)", out)
            if m:
                boot_sec = int(m.group(1))
                sec = int(time.time() - boot_sec)
                return f"{sec}s"
        except Exception:
            pass

    # 4. Fallback monotonic timer
    sec = int(time.monotonic())
    return f"{sec}s"


def _get_current_username() -> str:
    """Retrieves current user name cross-platform."""
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


class SystemInfoCollector(BaseCollector):
    """
    Forensic collector for 'system.info'.
    Collects hostname, OS, architecture, kernel version, uptime, and current username.
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        hostname = socket.gethostname() or "unknown"
        os_name = platform.system() or sys.platform
        architecture = platform.machine() or platform.architecture()[0]
        kernel = platform.release() or platform.version() or "unknown"
        uptime = _get_uptime_string()
        username = _get_current_username()

        return {
            "hostname": str(hostname),
            "os": str(os_name),
            "architecture": str(architecture),
            "kernel": str(kernel),
            "uptime": str(uptime),
            "username": str(username)
        }


class SystemUsersCollector(BaseCollector):
    """
    Forensic collector for 'system.users'.
    Safely and read-only enumerates local users on the endpoint.
    Handles permission or platform errors gracefully.
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        users: List[Dict[str, str]] = []
        seen_names = set()

        # 1. Unix / Linux / macOS (pwd database)
        try:
            import pwd
            for entry in pwd.getpwall():
                name = entry.pw_name
                # Exclude internal daemon / service accounts starting with '_' if on macOS, or keep valid users
                if name and name not in seen_names:
                    seen_names.add(name)
                    users.append({
                        "name": str(name),
                        "type": "local"
                    })
        except ImportError:
            # Not a Unix platform (e.g. Windows)
            pass
        except PermissionError:
            # Fall back to current user if pwd.getpwall is restricted
            pass
        except Exception:
            pass

        # 2. Windows fallback / enumeration
        if not users and platform.system() == "Windows":
            try:
                import ctypes
                from ctypes import wintypes

                # Attempt NetUserEnum or enumerate User profiles directory safely
                user_dir = os.environ.get("SystemDrive", "C:") + "\\Users"
                if os.path.exists(user_dir):
                    for entry in os.listdir(user_dir):
                        full_path = os.path.join(user_dir, entry)
                        if os.path.isdir(full_path) and entry not in ("Public", "Default", "All Users"):
                            if entry not in seen_names:
                                seen_names.add(entry)
                                users.append({
                                    "name": str(entry),
                                    "type": "local"
                                })
            except Exception:
                pass

        # 3. Graceful fallback: current active user
        if not users:
            curr_user = _get_current_username()
            if curr_user:
                users.append({
                    "name": str(curr_user),
                    "type": "local"
                })

        return {
            "users": users
        }
