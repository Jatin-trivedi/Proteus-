"""
REAL Forensic Functions - Python Implementations
These are used when compiling to Python (for testing)
"""

import platform
import subprocess
import json
import os
import sys

def collect_registry(hive: str) -> str:
    if platform.system() == "Windows":
        try:
            import winreg
            parts = hive.split("\\")
            hive_name = parts[0]
            key_path = "\\".join(parts[1:])
            
            hives = {
                "HKLM": winreg.HKEY_LOCAL_MACHINE,
                "HKCU": winreg.HKEY_CURRENT_USER,
                "HKCR": winreg.HKEY_CLASSES_ROOT,
                "HKU": winreg.HKEY_USERS,
            }
            
            if hive_name not in hives:
                return json.dumps({"error": f"Unknown hive: {hive_name}"})
            
            key = winreg.OpenKey(hives[hive_name], key_path)
            values = {}
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, index)
                    values[name] = str(value)
                    index += 1
                except WindowsError:
                    break
            
            winreg.CloseKey(key)
            return json.dumps(values)
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        return json.dumps({"error": "Registry collection only supported on Windows"})

def get_processes() -> str:
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'memory_mb': proc.info['memory_info'].rss / 1024 / 1024 if proc.info['memory_info'] else 0,
                    'cpu_percent': proc.info['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return json.dumps(processes)
    except ImportError:
        return json.dumps({"error": "psutil not installed"})

def get_system_info() -> str:
    info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version()
    }
    return json.dumps(info)

def scan_network() -> str:
    if platform.system() == "Windows":
        try:
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
            return json.dumps({'output': result.stdout})
        except Exception as e:
            return json.dumps({'error': str(e)})
    else:
        try:
            result = subprocess.run(['ifconfig', '-a'], capture_output=True, text=True)
            return json.dumps({'output': result.stdout})
        except Exception as e:
            return json.dumps({'error': str(e)})

def pack(*args) -> str:
    return json.dumps({
        'results': args,
        'count': len(args)
    })

def print_msg(msg: str) -> None:
    print(msg)