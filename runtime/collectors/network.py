"""
Proteus JOCKY Forensic Runtime - Network Forensic Collectors
Implements:
- network.interfaces()
- network.connections()
- network.routes()
- network.dns()
"""

import os
import sys
import platform
import subprocess
import socket
import re
from typing import Dict, Any, List, Optional

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode


class NetworkInterfacesCollector(BaseCollector):
    """
    Forensic collector for 'network.interfaces'.
    Collects network adapter information:
    - name (str)
    - addresses (list of IPv4/IPv6 strings)
    - mac (str)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        interfaces: List[Dict[str, Any]] = []

        # 1. psutil support if installed
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            for name, snics in addrs.items():
                ip_list = []
                mac_addr = ""
                for snic in snics:
                    # AF_INET, AF_INET6
                    if snic.family in (socket.AF_INET, socket.AF_INET6):
                        ip_list.append(snic.address)
                    elif hasattr(psutil, "AF_LINK") and snic.family == psutil.AF_LINK:
                        mac_addr = snic.address or ""
                interfaces.append({
                    "name": str(name),
                    "addresses": ip_list,
                    "mac": str(mac_addr)
                })
            if interfaces:
                return {"interfaces": interfaces}
        except ImportError:
            pass

        # 2. Windows: ipconfig /all
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["ipconfig", "/all"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
                curr_if: Optional[Dict[str, Any]] = None
                for line in out.splitlines():
                    if "adapter" in line.lower() and ":" in line:
                        if curr_if:
                            interfaces.append(curr_if)
                        name = line.split("adapter", 1)[1].split(":")[0].strip()
                        curr_if = {"name": name, "addresses": [], "mac": ""}
                    elif curr_if:
                        line_s = line.strip()
                        if "Physical Address" in line_s or "Description" in line_s:
                            if "Physical Address" in line_s:
                                curr_if["mac"] = line_s.split(":")[-1].strip().replace("-", ":")
                        elif "IPv4 Address" in line_s or "IPv6 Address" in line_s or "IP Address" in line_s:
                            ip = line_s.split(":")[-1].strip().split("(")[0].strip()
                            if ip and ip not in curr_if["addresses"]:
                                curr_if["addresses"].append(ip)

                if curr_if:
                    interfaces.append(curr_if)

                if interfaces:
                    return {"interfaces": interfaces}
            except Exception:
                pass

        # 3. Unix / Linux / macOS: ifconfig or ip addr
        try:
            out = subprocess.check_output(
                ["ifconfig"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            curr_if = None
            for line in out.splitlines():
                if line and not line.startswith("\t") and not line.startswith(" "):
                    if curr_if:
                        interfaces.append(curr_if)
                    name = line.split(":")[0].strip()
                    curr_if = {"name": name, "addresses": [], "mac": ""}
                elif curr_if:
                    line_s = line.strip()
                    if line_s.startswith("ether ") or line_s.startswith("lladdr "):
                        curr_if["mac"] = line_s.split()[1].strip()
                    elif line_s.startswith("inet "):
                        curr_if["addresses"].append(line_s.split()[1].strip())
                    elif line_s.startswith("inet6 "):
                        addr = line_s.split()[1].strip()
                        if "%" in addr:
                            addr = addr.split("%")[0]
                        curr_if["addresses"].append(addr)

            if curr_if:
                interfaces.append(curr_if)

            if interfaces:
                return {"interfaces": interfaces}
        except Exception:
            pass

        # 4. Fallback if no network command succeeds
        return {
            "interfaces": [
                {
                    "name": "lo0",
                    "addresses": ["127.0.0.1", "::1"],
                    "mac": ""
                }
            ]
        }


class NetworkConnectionsCollector(BaseCollector):
    """
    Forensic collector for 'network.connections'.
    Collects active sockets and established connections:
    - protocol (str)
    - local (str)
    - remote (str)
    - state (str)
    - pid (int)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        connections: List[Dict[str, Any]] = []

        # 1. psutil support if installed
        try:
            import psutil
            conns = psutil.net_connections(kind="inet")
            for c in conns:
                proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
                loc = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "*:*"
                rem = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "*:*"
                state = c.status or ("LISTEN" if proto == "TCP" and not c.raddr else "ESTABLISHED")
                pid = c.pid or 0
                connections.append({
                    "protocol": proto,
                    "local": loc,
                    "remote": rem,
                    "state": state,
                    "pid": pid
                })
            if connections:
                return {"connections": connections}
        except (ImportError, Exception):
            pass

        # 2. macOS / Unix: lsof -nP -iTCP -iUDP
        try:
            out = subprocess.check_output(
                ["lsof", "-nP", "-iTCP", "-iUDP"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            for line in out.strip().splitlines()[1:]:
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    proto_raw = parts[4].upper()
                    proto = "TCP" if "TCP" in proto_raw else "UDP"
                    pid_val = int(parts[1]) if parts[1].isdigit() else 0
                    name_col = parts[8].strip()

                    state = "ESTABLISHED"
                    m_state = re.search(r"\(([^)]+)\)", name_col)
                    if m_state:
                        state = m_state.group(1).upper()
                        name_clean = name_col[:m_state.start()].strip()
                    else:
                        name_clean = name_col

                    if "->" in name_clean:
                        loc, rem = name_clean.split("->", 1)
                    else:
                        loc = name_clean
                        rem = "*:*"

                    connections.append({
                        "protocol": proto,
                        "local": loc,
                        "remote": rem,
                        "state": state,
                        "pid": pid_val
                    })

            if connections:
                return {"connections": connections}
        except Exception:
            pass

        # 3. Generic netstat fallback (macOS/Linux/Windows)
        try:
            flags = ["-ano"] if platform.system() == "Windows" else ["-an"]
            out = subprocess.check_output(
                ["netstat"] + flags,
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[0].lower().startswith(("tcp", "udp")):
                    proto = parts[0].upper().replace("4", "").replace("6", "")
                    loc = parts[3] if len(parts) > 3 else "*:*"
                    rem = parts[4] if len(parts) > 4 else "*:*"
                    state = parts[5] if len(parts) > 5 else "ESTABLISHED"
                    pid = int(parts[-1]) if parts[-1].isdigit() else 0
                    connections.append({
                        "protocol": proto,
                        "local": loc,
                        "remote": rem,
                        "state": state,
                        "pid": pid
                    })

            if connections:
                return {"connections": connections}
        except Exception:
            pass

        return {"connections": connections}


class NetworkRoutesCollector(BaseCollector):
    """
    Forensic collector for 'network.routes'.
    Collects routing table entries:
    - destination (str)
    - gateway (str)
    - interface (str)
    - metric (int)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        routes: List[Dict[str, Any]] = []

        # 1. Windows: route print or netstat -r
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["route", "print"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
                start = False
                for line in out.splitlines():
                    if "Network Destination" in line and "Gateway" in line:
                        start = True
                        continue
                    if start:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                metric = int(parts[4])
                            except ValueError:
                                metric = 0
                            routes.append({
                                "destination": parts[0],
                                "gateway": parts[2],
                                "interface": parts[3],
                                "metric": metric
                            })
                        elif "Persistent Routes:" in line or "IPv6 Route Table" in line:
                            break
                if routes:
                    return {"routes": routes}
            except Exception:
                pass

        # 2. Linux: ip route
        if platform.system() == "Linux":
            try:
                out = subprocess.check_output(
                    ["ip", "route"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                for line in out.strip().splitlines():
                    parts = line.split()
                    if parts:
                        dest = parts[0]
                        gw = "0.0.0.0"
                        iface = "unknown"
                        metric = 0
                        if "via" in parts:
                            gw = parts[parts.index("via") + 1]
                        if "dev" in parts:
                            iface = parts[parts.index("dev") + 1]
                        if "metric" in parts:
                            try:
                                metric = int(parts[parts.index("metric") + 1])
                            except ValueError:
                                metric = 0
                        routes.append({
                            "destination": dest,
                            "gateway": gw,
                            "interface": iface,
                            "metric": metric
                        })
                if routes:
                    return {"routes": routes}
            except Exception:
                pass

        # 3. macOS / BSD: netstat -rn -f inet
        try:
            out = subprocess.check_output(
                ["netstat", "-rn", "-f", "inet"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            start = False
            for line in out.splitlines():
                if "Destination" in line and "Gateway" in line:
                    start = True
                    continue
                if not start or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    dest = parts[0]
                    gw = parts[1]
                    netif = parts[3] if len(parts) >= 4 else "unknown"
                    routes.append({
                        "destination": dest,
                        "gateway": gw,
                        "interface": netif,
                        "metric": 0
                    })

            if routes:
                return {"routes": routes}
        except Exception:
            pass

        # Fallback default route
        return {
            "routes": [
                {
                    "destination": "default",
                    "gateway": "127.0.0.1",
                    "interface": "lo0",
                    "metric": 0
                }
            ]
        }


class NetworkDnsCollector(BaseCollector):
    """
    Forensic collector for 'network.dns'.
    Collects configured DNS resolvers, search domains, and configuration metadata:
    - dns_servers (list of str)
    - search_domains (list of str)
    - configuration (dict)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        dns_servers: List[str] = []
        search_domains: List[str] = []
        config: Dict[str, Any] = {}

        # 1. macOS: scutil --dns
        if platform.system() == "Darwin":
            try:
                out = subprocess.check_output(
                    ["scutil", "--dns"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                for line in out.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("nameserver["):
                        srv = line_s.split(":", 1)[1].strip()
                        if srv and srv not in dns_servers:
                            dns_servers.append(srv)
                    elif line_s.startswith("search domain[") or line_s.startswith("domain :"):
                        dom = line_s.split(":", 1)[1].strip()
                        if dom and dom not in search_domains:
                            search_domains.append(dom)
                config["source"] = "scutil"
            except Exception:
                pass

        # 2. Linux / Unix / macOS fallback: /etc/resolv.conf
        if os.path.exists("/etc/resolv.conf"):
            try:
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        line_s = line.strip()
                        if line_s.startswith("nameserver"):
                            parts = line_s.split()
                            if len(parts) > 1 and parts[1] not in dns_servers:
                                dns_servers.append(parts[1])
                        elif line_s.startswith("search") or line_s.startswith("domain"):
                            parts = line_s.split()
                            for d in parts[1:]:
                                if d not in search_domains:
                                    search_domains.append(d)
                        elif line_s.startswith("options"):
                            config["options"] = line_s.split()[1:]
                if not config.get("source"):
                    config["source"] = "/etc/resolv.conf"
            except Exception:
                pass

        # 3. Windows: ipconfig /all
        if platform.system() == "Windows" and not dns_servers:
            try:
                out = subprocess.check_output(
                    ["ipconfig", "/all"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                in_dns = False
                for line in out.splitlines():
                    line_s = line.strip()
                    if "DNS Servers" in line_s:
                        in_dns = True
                        srv = line_s.split(":")[-1].strip()
                        if srv and srv not in dns_servers:
                            dns_servers.append(srv)
                    elif in_dns:
                        if ":" in line_s:
                            in_dns = False
                        else:
                            srv = line_s.strip()
                            if srv and srv not in dns_servers:
                                dns_servers.append(srv)
                    if "Primary Dns Suffix" in line_s:
                        suffix = line_s.split(":")[-1].strip()
                        if suffix and suffix not in search_domains:
                            search_domains.append(suffix)
                config["source"] = "ipconfig"
            except Exception:
                pass

        return {
            "dns_servers": dns_servers,
            "search_domains": search_domains,
            "configuration": config
        }
