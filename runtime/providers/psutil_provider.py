"""
Proteus JOCKY Forensic Runtime — psutil Cross-Platform Provider

Provides psutil-based implementations of ProcessProvider and NetworkProvider.
If psutil is available on the target environment, this provides fast, reliable,
and OS-independent data collection before falling back to native shell commands/APIs.
"""

import datetime
import socket
from typing import Any, Dict, List, Optional

from runtime.errors import CollectorException, ErrorCode
from runtime.providers.base_provider import NetworkProvider, ProcessProvider


class PsutilProcessProvider(ProcessProvider):
    """Process provider leveraging psutil library."""

    def __init__(self):
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            self._psutil = None

    @property
    def is_available(self) -> bool:
        return self._psutil is not None

    def list_processes(self) -> List[Dict[str, Any]]:
        if not self._psutil:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message="psutil is not available"
            )

        processes = []
        try:
            for p in self._psutil.process_iter(["pid", "name", "ppid", "username"]):
                try:
                    info = p.info
                    processes.append({
                        "pid": int(info.get("pid") or 0),
                        "name": str(info.get("name") or "unknown"),
                        "parent_pid": int(info.get("ppid") or 0),
                        "username": str(info.get("username") or "unknown"),
                    })
                except (self._psutil.NoSuchProcess, self._psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"psutil process enumeration failed: {e}"
            )

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        if not self._psutil:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message="psutil is not available"
            )

        try:
            proc = self._psutil.Process(pid)
            try:
                name = proc.name() or "unknown"
            except Exception:
                name = "unknown"

            try:
                ppid = proc.ppid() or 0
            except Exception:
                ppid = 0

            try:
                ctime = proc.create_time()
                dt = datetime.datetime.fromtimestamp(ctime, tz=datetime.timezone.utc)
                start_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                start_time = "unknown"

            try:
                exe = proc.exe() or "unknown"
            except (self._psutil.AccessDenied, PermissionError):
                exe = "[access denied]"
            except Exception:
                exe = "unknown"

            return {
                "pid": pid,
                "name": name,
                "parent_pid": ppid,
                "start_time": start_time,
                "executable": exe,
            }
        except self._psutil.NoSuchProcess:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Process with PID {pid} does not exist"
            )
        except self._psutil.AccessDenied:
            raise CollectorException(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"Access denied querying process {pid}"
            )
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"psutil failed querying PID {pid}: {e}"
            )


class PsutilNetworkProvider(NetworkProvider):
    """Network provider leveraging psutil library."""

    def __init__(self):
        try:
            import psutil
            self._psutil = psutil
        except ImportError:
            self._psutil = None

    @property
    def is_available(self) -> bool:
        return self._psutil is not None

    def get_interfaces(self) -> List[Dict[str, Any]]:
        if not self._psutil:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message="psutil is not available"
            )

        try:
            addrs = self._psutil.net_if_addrs()
            interfaces = []
            for name, snic_list in addrs.items():
                ip_addrs = []
                mac_addr = "unknown"
                for snic in snic_list:
                    if snic.family in (socket.AF_INET, getattr(socket, "AF_INET6", -1)):
                        ip_addrs.append(snic.address)
                    elif hasattr(self._psutil, "AF_LINK") and snic.family == self._psutil.AF_LINK:
                        mac_addr = snic.address or "unknown"
                    elif hasattr(socket, "AF_PACKET") and snic.family == socket.AF_PACKET:
                        mac_addr = snic.address or "unknown"
                interfaces.append({
                    "name": name,
                    "addresses": ip_addrs,
                    "mac": mac_addr,
                })
            return interfaces
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"psutil net_if_addrs failed: {e}"
            )

    def get_connections(self) -> List[Dict[str, Any]]:
        if not self._psutil:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message="psutil is not available"
            )

        try:
            conns = self._psutil.net_connections(kind="inet")
            results = []
            for c in conns:
                proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
                l_str = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "0.0.0.0:0"
                if c.raddr:
                    r_str = f"{c.raddr.ip}:{c.raddr.port}"
                else:
                    r_str = "*:*"
                results.append({
                    "protocol": proto,
                    "local": l_str,
                    "remote": r_str,
                    "state": str(c.status or "UNKNOWN"),
                    "pid": int(c.pid or 0),
                })
            return results
        except (self._psutil.AccessDenied, PermissionError):
            raise CollectorException(
                code=ErrorCode.PERMISSION_DENIED,
                message="Access denied querying network connections via psutil"
            )
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"psutil net_connections failed: {e}"
            )

    def get_routes(self) -> List[Dict[str, Any]]:
        raise CollectorException(
            code=ErrorCode.NOT_IMPLEMENTED,
            message="psutil does not provide routing table enumeration"
        )

    def get_dns(self) -> Dict[str, Any]:
        raise CollectorException(
            code=ErrorCode.NOT_IMPLEMENTED,
            message="psutil does not provide DNS configuration enumeration"
        )
