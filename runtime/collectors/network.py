"""
Proteus JOCKY Forensic Runtime - Network Forensic Collectors
Implements:
- network.interfaces()
- network.connections()
- network.routes()
- network.dns()

Delegates platform-specific data acquisition to ForensicProvider.
"""

from typing import Any, Dict, List, Optional

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
    from runtime.providers import NetworkProvider, get_default_network_provider
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode
    from providers import NetworkProvider, get_default_network_provider


class NetworkInterfacesCollector(BaseCollector):
    """
    Forensic collector for 'network.interfaces'.
    Collects network adapter information:
    - name (str)
    - addresses (list of IPv4/IPv6 strings)
    - mac (str)
    """

    def __init__(self, provider: Optional[NetworkProvider] = None):
        self.provider = provider or get_default_network_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        interfaces = self.provider.get_interfaces()
        return {"interfaces": interfaces}


class NetworkConnectionsCollector(BaseCollector):
    """
    Forensic collector for 'network.connections'.
    Collects active TCP/UDP sockets and connections:
    - protocol (str)
    - local (str)
    - remote (str)
    - state (str)
    - pid (int)
    """

    def __init__(self, provider: Optional[NetworkProvider] = None):
        self.provider = provider or get_default_network_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        connections = self.provider.get_connections()
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

    def __init__(self, provider: Optional[NetworkProvider] = None):
        self.provider = provider or get_default_network_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        routes = self.provider.get_routes()
        return {"routes": routes}


class NetworkDnsCollector(BaseCollector):
    """
    Forensic collector for 'network.dns'.
    Collects DNS resolver configuration:
    - dns_servers (list of IP strings)
    - search_domains (list of domain strings)
    - configuration (dict)
    """

    def __init__(self, provider: Optional[NetworkProvider] = None):
        self.provider = provider or get_default_network_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return self.provider.get_dns()
