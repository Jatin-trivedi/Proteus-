"""
Proteus JOCKY Forensic Runtime - Process Forensic Collectors
Implements:
- processes.list()
- processes.details(pid)

Delegates platform-specific data acquisition to ForensicProvider.
"""

from typing import Any, Dict, List, Optional

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
    from runtime.providers import ProcessProvider, get_default_process_provider
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode
    from providers import ProcessProvider, get_default_process_provider


class ProcessesListCollector(BaseCollector):
    """
    Forensic collector for 'processes.list'.
    Enumerates running processes and returns a list of dictionaries with:
    - pid (int)
    - name (str)
    - parent_pid (int)
    - username (str)
    """

    def __init__(self, provider: Optional[ProcessProvider] = None):
        self.provider = provider or get_default_process_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        processes = self.provider.list_processes()
        return {"processes": processes}


class ProcessesDetailsCollector(BaseCollector):
    """
    Forensic collector for 'processes.details(pid)'.
    Retrieves detailed information for a specific PID:
    - pid (int)
    - name (str)
    - parent_pid (int)
    - start_time (str)
    - executable (str)
    """

    def __init__(self, provider: Optional[ProcessProvider] = None):
        self.provider = provider or get_default_process_provider()

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if "pid" not in parameters or parameters["pid"] is None:
            raise CollectorException(
                code=ErrorCode.INVALID_PARAMETERS,
                message="Missing required parameter 'pid' for processes.details",
            )

        try:
            pid = int(parameters["pid"])
        except (ValueError, TypeError):
            raise CollectorException(
                code=ErrorCode.INVALID_PARAMETERS,
                message=f"Invalid PID parameter: {parameters.get('pid')!r}. Expected an integer.",
            )

        return self.provider.get_process_details(pid)
