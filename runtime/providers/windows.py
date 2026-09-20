"""
Proteus JOCKY Forensic Runtime — Windows Platform Provider

Provides native Windows forensic data acquisition:
- System: Win32 GetTickCount64, C:\\Users folder enumeration
- Processes: tasklist CLI parsing
- Network: ipconfig /all, netstat -ano, route print
"""

import csv
import getpass
import io
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


class WindowsSystemProvider(SystemProvider):
    """Windows system provider."""

    def get_hostname(self) -> str:
        try:
            return socket.gethostname() or "unknown"
        except Exception:
            return "unknown"

    def get_os(self) -> str:
        return platform.system() or "Windows"

    def get_architecture(self) -> str:
        return platform.machine() or "unknown"

    def get_kernel(self) -> str:
        return platform.version() or platform.release() or "unknown"

    def get_uptime(self) -> str:
        try:
            import ctypes
            msec = ctypes.windll.kernel32.GetTickCount64()
            seconds = int(msec / 1000)
            return f"{seconds}s"
        except Exception:
            pass

        seconds = int(time.monotonic())
        return f"{seconds}s"

    def get_username(self) -> str:
        try:
            return (
                os.environ.get("USERNAME")
                or getpass.getuser()
                or "unknown"
            )
        except Exception:
            return "unknown"

    def get_users(self) -> List[Dict[str, str]]:
        users = []
        try:
            system_drive = os.environ.get("SystemDrive", "C:")
            users_dir = os.path.join(system_drive, "\\Users")
            if os.path.exists(users_dir):
                for entry in os.listdir(users_dir):
                    entry_path = os.path.join(users_dir, entry)
                    if os.path.isdir(entry_path):
                        if entry.lower() not in (
                            "public", "default", "default user", "all users", "desktop.ini"
                        ):
                            users.append({
                                "name": entry,
                                "type": "local",
                            })
        except Exception:
            pass

        if not users:
            curr_user = self.get_username()
            users.append({"name": curr_user, "type": "local"})

        return users


class WindowsProcessProvider(ProcessProvider):
    """Windows process provider via tasklist CLI."""

    def list_processes(self) -> List[Dict[str, Any]]:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            reader = csv.reader(io.StringIO(out))
            processes = []
            for row in reader:
                if len(row) >= 2:
                    name = row[0].strip()
                    try:
                        pid = int(row[1].strip())
                        user = row[6].strip() if len(row) > 6 else "unknown"
                        processes.append({
                            "pid": pid,
                            "name": name,
                            "parent_pid": 0,
                            "username": user,
                        })
                    except ValueError:
                        continue
            if processes:
                return processes
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Failed to enumerate processes on Windows: {e}",
            )

        raise CollectorException(
            code=ErrorCode.COLLECTION_FAILED,
            message="No processes found via tasklist command",
        )

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            if "No tasks are running" in out or "INFO:" in out:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Process with PID {pid} does not exist",
                )

            reader = csv.reader(io.StringIO(out))
            for row in reader:
                if len(row) >= 2:
                    try:
                        r_pid = int(row[1].strip())
                        if r_pid == pid:
                            name = row[0].strip()
                            return {
                                "pid": pid,
                                "name": name,
                                "parent_pid": 0,
                                "start_time": "unknown",
                                "executable": name,
                            }
                    except ValueError:
                        continue

            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Process with PID {pid} not found in tasklist output",
            )
        except subprocess.CalledProcessError:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Process with PID {pid} does not exist",
            )
        except CollectorException:
            raise
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Error querying process {pid} on Windows: {e}",
            )


class WindowsNetworkProvider(NetworkProvider):
    """Windows network provider via ipconfig, netstat, route print."""

    def get_interfaces(self) -> List[Dict[str, Any]]:
        interfaces = []
        try:
            out = subprocess.check_output(
                ["ipconfig", "/all"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            current_iface = None
            current_addrs = []
            current_mac = "unknown"

            for line in out.splitlines():
                if line and not line.startswith(" ") and ":" in line:
                    if current_iface:
                        interfaces.append({
                            "name": current_iface,
                            "addresses": current_addrs,
                            "mac": current_mac,
                        })
                    current_iface = line.split(":")[0].strip()
                    current_addrs = []
                    current_mac = "unknown"
                    continue

                m_mac = re.search(r"Physical Address[ .]*:\s*([0-9A-Fa-f\-]{17})", line)
                if m_mac:
                    current_mac = m_mac.group(1).replace("-", ":").lower()

                m_ip = re.search(r"IPv[46] Address[ .]*:\s*([0-9a-fA-F\.\:]+)", line)
                if m_ip:
                    clean_ip = m_ip.group(1).replace("(Preferred)", "").strip()
                    current_addrs.append(clean_ip)

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

        return [{
            "name": "Ethernet",
            "addresses": ["127.0.0.1"],
            "mac": "00:00:00:00:00:00",
        }]

    def get_connections(self) -> List[Dict[str, Any]]:
        connections = []
        try:
            out = subprocess.check_output(
                ["netstat", "-ano"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0].upper() in ("TCP", "UDP"):
                    proto = parts[0].upper()
                    l_str = parts[1]
                    r_str = parts[2]
                    state = "UNKNOWN"
                    pid = 0
                    if proto == "TCP" and len(parts) >= 5:
                        state = parts[3]
                        try:
                            pid = int(parts[4])
                        except ValueError:
                            pid = 0
                    elif proto == "UDP" and len(parts) >= 4:
                        state = "UNKNOWN"
                        try:
                            pid = int(parts[3])
                        except ValueError:
                            pid = 0
                    connections.append({
                        "protocol": proto,
                        "local": l_str,
                        "remote": r_str,
                        "state": state,
                        "pid": pid,
                    })
            if connections:
                return connections
        except Exception:
            pass

        return connections

    def get_routes(self) -> List[Dict[str, Any]]:
        routes = []
        try:
            out = subprocess.check_output(
                ["route", "print"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            in_active_routes = False
            for line in out.splitlines():
                if "Active Routes:" in line or "Network Destination" in line:
                    in_active_routes = True
                    continue
                if in_active_routes:
                    if "Persistent Routes:" in line or "IPv6 Route Table" in line or not line.strip():
                        if "IPv6" in line or "Persistent" in line:
                            break
                        continue
                    parts = line.split()
                    if len(parts) >= 5:
                        dest = parts[0]
                        gateway = parts[2]
                        iface = parts[3]
                        try:
                            metric = int(parts[4])
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

        return [{
            "destination": "0.0.0.0",
            "gateway": "0.0.0.0",
            "interface": "127.0.0.1",
            "metric": 0,
        }]

    def get_dns(self) -> Dict[str, Any]:
        dns_servers = []
        search_domains = []
        config = {}

        try:
            out = subprocess.check_output(
                ["ipconfig", "/all"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode("utf-8", errors="ignore")

            in_dns_section = False
            for line in out.splitlines():
                m_dns = re.search(r"DNS Servers[ .]*:\s*([0-9a-fA-F\.\:]+)", line)
                if m_dns:
                    in_dns_section = True
                    dns = m_dns.group(1).strip()
                    if dns and dns not in dns_servers:
                        dns_servers.append(dns)
                    continue

                if in_dns_section:
                    m_next = re.search(r"^\s+([0-9a-fA-F\.\:]+)$", line)
                    if m_next:
                        dns = m_next.group(1).strip()
                        if dns and dns not in dns_servers:
                            dns_servers.append(dns)
                    else:
                        if line.strip() and ":" in line:
                            in_dns_section = False

                m_suffix = re.search(r"Primary Dns Suffix[ .]*:\s*([a-zA-Z0-9\.\-]+)", line)
                if m_suffix:
                    suffix = m_suffix.group(1).strip()
                    if suffix and suffix not in search_domains:
                        search_domains.append(suffix)

            if dns_servers or search_domains:
                config["source"] = "ipconfig"
        except Exception:
            pass

        return {
            "dns_servers": dns_servers,
            "search_domains": search_domains,
            "configuration": config,
        }
