"""
Proteus JOCKY Forensic Runtime - Process Forensic Collectors
Implements:
- processes.list()
- processes.details(pid)
"""

import os
import sys
import platform
import subprocess
import re
from typing import Dict, Any, List, Optional

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode


class ProcessesListCollector(BaseCollector):
    """
    Forensic collector for 'processes.list'.
    Enumerates running processes and returns a list of dictionaries with:
    - pid (int)
    - name (str)
    - parent_pid (int)
    - username (str)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        processes: List[Dict[str, Any]] = []

        # 1. psutil support if installed
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'ppid', 'username']):
                try:
                    info = proc.info
                    processes.append({
                        "pid": int(info['pid']),
                        "name": str(info['name'] or ""),
                        "parent_pid": int(info['ppid'] or 0),
                        "username": str(info['username'] or "unknown")
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return {"processes": processes}
        except ImportError:
            pass

        # 2. Windows fallback using tasklist
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["tasklist", "/FO", "CSV", "/NH"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
                for line in out.strip().splitlines():
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) >= 2:
                        try:
                            pid_val = int(parts[1])
                            proc_name = parts[0]
                            user = os.environ.get("USERNAME", "unknown")
                            processes.append({
                                "pid": pid_val,
                                "name": proc_name,
                                "parent_pid": 0,
                                "username": user
                            })
                        except ValueError:
                            continue
                return {"processes": processes}
            except Exception as e:
                # If command fails, return fallback or raise CollectorException
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Failed to enumerate processes on Windows: {e}"
                )

        # 3. Unix / Linux / macOS fallback using ps
        try:
            out = subprocess.check_output(
                ["ps", "-axo", "pid=,ppid=,user=,comm="],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            for line in out.strip().splitlines():
                parts = line.strip().split(None, 3)
                if len(parts) >= 4:
                    try:
                        pid_val = int(parts[0])
                        ppid_val = int(parts[1])
                        user_val = parts[2]
                        comm_val = os.path.basename(parts[3])
                        processes.append({
                            "pid": pid_val,
                            "name": comm_val,
                            "parent_pid": ppid_val,
                            "username": user_val
                        })
                    except ValueError:
                        continue
            return {"processes": processes}
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Failed to enumerate processes via ps: {e}"
            )


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

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if "pid" not in parameters or parameters["pid"] is None:
            raise CollectorException(
                code=ErrorCode.INVALID_PARAMETERS,
                message="Missing required parameter 'pid' for processes.details"
            )

        try:
            pid = int(parameters["pid"])
        except (ValueError, TypeError):
            raise CollectorException(
                code=ErrorCode.INVALID_PARAMETERS,
                message=f"Invalid PID parameter: {parameters.get('pid')!r}. Expected an integer."
            )

        # 1. psutil support if installed
        try:
            import psutil
            try:
                proc = psutil.Process(pid)
                import datetime
                start_str = datetime.datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                try:
                    exe = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    exe = proc.name()

                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "parent_pid": proc.ppid() or 0,
                    "start_time": start_str,
                    "executable": str(exe or proc.name())
                }
            except psutil.NoSuchProcess:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Process with PID {pid} does not exist"
                )
            except psutil.AccessDenied:
                raise CollectorException(
                    code=ErrorCode.PERMISSION_DENIED,
                    message=f"Access denied querying process with PID {pid}"
                )
        except ImportError:
            pass

        # 2. Unix / Linux / macOS using ps
        if platform.system() != "Windows":
            try:
                # ps -p <pid> -o pid=,ppid=,lstart=,command=
                out = subprocess.check_output(
                    ["ps", "-p", str(pid), "-o", "pid=,ppid=,lstart=,command="],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).strip()

                if not out:
                    raise CollectorException(
                        code=ErrorCode.COLLECTION_FAILED,
                        message=f"Process with PID {pid} does not exist"
                    )

                parts = out.split(None, 7)
                if len(parts) >= 8:
                    pid_val = int(parts[0])
                    ppid_val = int(parts[1])
                    start_time = " ".join(parts[2:7])
                    cmd = parts[7].strip()
                    exec_path = cmd.split()[0] if cmd else ""
                    name = os.path.basename(exec_path) if exec_path else f"pid_{pid_val}"
                    return {
                        "pid": pid_val,
                        "name": name,
                        "parent_pid": ppid_val,
                        "start_time": start_time,
                        "executable": exec_path
                    }
                elif len(parts) >= 3:
                    # Fallback for short parsing
                    return {
                        "pid": int(parts[0]),
                        "name": f"pid_{parts[0]}",
                        "parent_pid": int(parts[1]),
                        "start_time": "unknown",
                        "executable": "unknown"
                    }
                else:
                    raise CollectorException(
                        code=ErrorCode.COLLECTION_FAILED,
                        message=f"Unexpected ps output for PID {pid}: {out}"
                    )
            except subprocess.CalledProcessError:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Process with PID {pid} does not exist or exited"
                )
            except CollectorException:
                raise
            except Exception as e:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Error querying process {pid}: {e}"
                )

        # 3. Windows fallback
        try:
            # Query tasklist for PID
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=5
            ).strip()

            if not out or "No tasks are running" in out:
                raise CollectorException(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Process with PID {pid} does not exist"
                )

            parts = [p.strip('"') for p in out.splitlines()[0].split('","')]
            proc_name = parts[0]
            return {
                "pid": pid,
                "name": proc_name,
                "parent_pid": 0,
                "start_time": "unknown",
                "executable": proc_name
            }
        except subprocess.CalledProcessError:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Process with PID {pid} does not exist"
            )
        except CollectorException:
            raise
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Error querying process {pid} on Windows: {e}"
            )
