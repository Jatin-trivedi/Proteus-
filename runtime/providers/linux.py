"""
Proteus JOCKY Forensic Runtime — Linux / Unix Platform Provider

Provides Linux (and Unix / macOS fallback) forensic data acquisition:
- System: /proc/uptime, pwd database, standard platform info
- Processes: ps CLI parsing
- Network: ifconfig / ip addr, netstat, ip route, /etc/resolv.conf
"""

import getpass
import os
import platform
import re
import socket
import subprocess
import time
from typing import Any, Dict, List

from runtime.errors import CollectorException, ErrorCode
from runtime.providers.base_provider import (
    NetworkProvider,
    ProcessProvider,
    SystemProvider,
)


class LinuxSystemProvider(SystemProvider):
    """Linux system provider."""

    def get_hostname(self) -> str:
        try:
            return socket.gethostname() or "unknown"
        except Exception:
            return "unknown"

    def get_os(self) -> str:
        return platform.system() or "Linux"

    def get_architecture(self) -> str:
        return platform.machine() or "unknown"

    def get_kernel(self) -> str:
        return platform.release() or "unknown"

    def get_uptime(self) -> str:
        # 1. /proc/uptime (standard Linux)
        if os.path.exists("/proc/uptime"):
            try:
                with open("/proc/uptime", "r") as f:
                    content = f.read().strip()
                    if content:
                        seconds = int(float(content.split()[0]))
                        return f"{seconds}s"
            except Exception:
                pass

        # 2. sysctl (macOS / BSD fallback)
        if platform.system() in ("Darwin", "FreeBSD", "OpenBSD"):
            try:
                out = subprocess.check_output(
                    ["sysctl", "-n", "kern.boottime"],
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                ).decode("utf-8")
                m = re.search(r"sec\s*=\s*(\d+)", out)
                if m:
                    boot_sec = int(m.group(1))
                    curr_sec = int(time.time())
                    diff = max(0, curr_sec - boot_sec)
                    return f"{diff}s"
            except Exception:
                pass

        # 3. Monotonic clock fallback
        seconds = int(time.monotonic())
        return f"{seconds}s"

    def get_username(self) -> str:
        try:
            return getpass.getuser()
        except Exception:
            return (
                os.environ.get("USER")
                or os.environ.get("LOGNAME")
                or "unknown"
            )

    def get_users(self) -> List[Dict[str, str]]:
        users = []
        try:
            import pwd
            for entry in pwd.getpwall():
                users.append({
                    "name": entry.pw_name,
                    "type": "local",
                })
        except (ImportError, AttributeError, PermissionError):
            pass

        if not users:
            curr_user = self.get_username()
            users.append({"name": curr_user, "type": "local"})

        return users


class LinuxProcessProvider(ProcessProvider):
    """Linux process provider via ps CLI."""

    def list_processes(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(
                ["ps", "-axo", "pid=,ppid=,user=,comm="],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")
            processes = []
            for line in out.strip().splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    try:
                        pid = int(parts[0])
                        ppid = int(parts[1])
                        user = parts[2]
                        name = parts[3].strip()
                        processes.append({
                            "pid": pid,
                            "name": name,
                            "parent_pid": ppid,
                            "username": user,
                        })
                    except ValueError:
                        continue
            if processes:
                return processes
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Failed to enumerate processes on Linux/Unix: {e}",
            )

        raise CollectorException(
            code=ErrorCode.COLLECTION_FAILED,
            message="No processes found via ps command",
        )

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        try:
            out = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "pid=,ppid=,lstart=,command="],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8").strip()

            if not out:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Process with PID {pid} does not exist",
                )

            parts = out.split(None, 7)
            if len(parts) >= 8:
                pid_val = int(parts[0])
                ppid = int(parts[1])
                start_time_str = " ".join(parts[2:7])
                cmd = parts[7].strip()
                exec_path = cmd.split()[0] if cmd else ""
                name = os.path.basename(exec_path) if exec_path else f"pid_{pid_val}"

                return {
                    "pid": pid,
                    "name": name,
                    "parent_pid": ppid,
                    "start_time": start_time_str,
                    "executable": cmd,
                }
            else:
                return {
                    "pid": pid,
                    "name": "unknown",
                    "parent_pid": 0,
                    "start_time": "unknown",
                    "executable": out,
                }
        except subprocess.CalledProcessError:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Process with PID {pid} does not exist",
            )
        except CollectorException:
            raise
        except PermissionError:
            raise CollectorException(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"Access denied querying process {pid}",
            )
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Error querying process {pid} on Linux/Unix: {e}",
            )


class LinuxNetworkProvider(NetworkProvider):
    """Linux network provider via standard utilities & /etc/resolv.conf."""

    def get_interfaces(self) -> List[Dict[str, Any]]:
        interfaces = []
        try:
            out = subprocess.check_output(
                ["ifconfig"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")

            current_iface = None
            current_addrs = []
            current_mac = "unknown"

            for line in out.splitlines():
                m_hdr = re.match(r"^([a-zA-Z0-9_\-\.]+):?\s+flags=", line)
                if not m_hdr:
                    m_hdr = re.match(r"^([a-zA-Z0-9_\-\.]+)\s+Link encap", line)

                if m_hdr:
                    if current_iface:
                        interfaces.append({
                            "name": current_iface,
                            "addresses": current_addrs,
                            "mac": current_mac,
                        })
                    current_iface = m_hdr.group(1)
                    current_addrs = []
                    current_mac = "unknown"
                    continue

                m_inet = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", line)
                if m_inet:
                    current_addrs.append(m_inet.group(1))

                m_inet6 = re.search(r"inet6\s+([a-fA-F0-9:]+)", line)
                if m_inet6:
                    current_addrs.append(m_inet6.group(1).split("%")[0])

                m_mac = re.search(r"(?:ether|HWaddr|lladdr)\s+([0-9a-fA-F:]{17})", line)
                if m_mac:
                    current_mac = m_mac.group(1).lower()

            if current_iface:
                interfaces.append({
                    "name": current_iface,
                    "addresses": current_addrs,
                    "mac": current_mac,
                })

            if interfaces:
                return interfaces
        except Exception:
            pass

        # Fallback loopback
        return [{
            "name": "lo0",
            "addresses": ["127.0.0.1", "::1"],
            "mac": "00:00:00:00:00:00",
        }]

    def get_connections(self) -> List[Dict[str, Any]]:
        connections = []
        try:
            out = subprocess.check_output(
                ["lsof", "-nP", "-iTCP", "-iUDP"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")

            lines = out.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        try:
                            pid = int(parts[1])
                            node = parts[7]
                            name = parts[8]
                            proto = "TCP" if "TCP" in node.upper() else ("UDP" if "UDP" in node.upper() else "TCP")
                            state = "UNKNOWN"
                            if "->" in name:
                                l_str, r_str = name.split("->", 1)
                            else:
                                l_str = name
                                r_str = "*:*"
                            if len(parts) >= 10 and "(" in parts[9]:
                                state = parts[9].strip("()")
                            connections.append({
                                "protocol": proto,
                                "local": l_str,
                                "remote": r_str,
                                "state": state,
                                "pid": pid,
                            })
                        except (ValueError, IndexError):
                            continue
            if connections:
                return connections
        except Exception:
            pass

        try:
            out = subprocess.check_output(
                ["netstat", "-an"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")

            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0].lower().startswith(("tcp", "udp")):
                    proto = parts[0].upper()
                    l_str = parts[3]
                    r_str = parts[4] if len(parts) > 4 else "*:*"
                    state = parts[5] if len(parts) > 5 and not parts[5].isdigit() else "UNKNOWN"
                    connections.append({
                        "protocol": proto,
                        "local": l_str,
                        "remote": r_str,
                        "state": state,
                        "pid": 0,
                    })
        except Exception:
            pass

        return connections

    def get_routes(self) -> List[Dict[str, Any]]:
        routes = []
        # Linux: ip route
        try:
            out = subprocess.check_output(
                ["ip", "route"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")
            for line in out.splitlines():
                parts = line.strip().split()
                if not parts:
                    continue
                dest = parts[0]
                gateway = "0.0.0.0"
                iface = "unknown"
                metric = 0
                for i, p in enumerate(parts):
                    if p == "via" and i + 1 < len(parts):
                        gateway = parts[i + 1]
                    elif p == "dev" and i + 1 < len(parts):
                        iface = parts[i + 1]
                    elif p == "metric" and i + 1 < len(parts):
                        try:
                            metric = int(parts[i + 1])
                        except ValueError:
                            metric = 0
                routes.append({
                    "destination": dest,
                    "gateway": gateway,
                    "interface": iface,
                    "metric": metric,
                })
            if routes:
                return routes
        except Exception:
            pass

        # macOS / BSD: netstat -rn -f inet
        try:
            out = subprocess.check_output(
                ["netstat", "-rn", "-f", "inet"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8")
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 6 and not parts[0].startswith("Destination") and not parts[0].startswith("Routing"):
                    dest = parts[0]
                    gateway = parts[1]
                    iface = parts[5] if len(parts) > 5 else "unknown"
                    routes.append({
                        "destination": dest,
                        "gateway": gateway,
                        "interface": iface,
                        "metric": 0,
                    })
            if routes:
                return routes
        except Exception:
            pass

        return [{
            "destination": "default",
            "gateway": "0.0.0.0",
            "interface": "lo0",
            "metric": 0,
        }]

    def get_dns(self) -> Dict[str, Any]:
        dns_servers = []
        search_domains = []
        config = {}

        # macOS: scutil --dns
        if platform.system() == "Darwin":
            try:
                out = subprocess.check_output(
                    ["scutil", "--dns"],
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                ).decode("utf-8")
                for line in out.splitlines():
                    m_ns = re.search(r"nameserver\[\d+\]\s*:\s*([a-fA-F0-9\.\:]+)", line)
                    if m_ns:
                        ns = m_ns.group(1).strip()
                        if ns not in dns_servers:
                            dns_servers.append(ns)
                    m_sd = re.search(r"search domain\[\d+\]\s*:\s*([a-zA-Z0-9\.\-]+)", line)
                    if m_sd:
                        sd = m_sd.group(1).strip()
                        if sd not in search_domains:
                            search_domains.append(sd)
                if dns_servers or search_domains:
                    config["source"] = "scutil"
            except Exception:
                pass

        # /etc/resolv.conf
        if not dns_servers and os.path.exists("/etc/resolv.conf"):
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("nameserver"):
                            parts = line.split()
                            if len(parts) >= 2 and parts[1] not in dns_servers:
                                dns_servers.append(parts[1])
                        elif line.startswith("search") or line.startswith("domain"):
                            parts = line.split()
                            for d in parts[1:]:
                                if d not in search_domains:
                                    search_domains.append(d)
                if dns_servers or search_domains:
                    config["source"] = "/etc/resolv.conf"
            except Exception:
                pass

        return {
            "dns_servers": dns_servers,
            "search_domains": search_domains,
            "configuration": config,
        }
