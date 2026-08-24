"""
Forensic function implementations.
These will be linked to the final executable.
"""

import platform
import subprocess
import json

def collect_registry(hive: str) -> str:
    """Collect Windows registry keys"""
    if platform.system() == "Windows":
        try:
            import winreg
            # Parse hive path
            parts = hive.split("\\")
            hive_name = parts[0]
            key_path = "\\".join(parts[1:])
            
            # Map hive names
            hives = {
                "HKLM": winreg.HKEY_LOCAL_MACHINE,
                "HKCU": winreg.HKEY_CURRENT_USER,
                "HKCR": winreg.HKEY_CLASSES_ROOT,
                "HKU": winreg.HKEY_USERS,
            }
            
            if hive_name not in hives:
                return json.dumps({"error": f"Unknown hive: {hive_name}"})
            
            # Open key and read values
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
    """Get list of running processes"""
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
    """Get system information"""
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
    """Scan network interfaces"""
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

def capture_packets(interface: str) -> str:
    """Capture network packets (stub - requires pcap)"""
    return json.dumps({
        'interface': interface,
        'status': 'not_implemented',
        'message': 'Packet capture requires WinPcap/Npcap or libpcap'
    })

def pack(*args) -> str:
    """Pack multiple values into a single JSON result"""
    return json.dumps({
        'results': args,
        'count': len(args)
    })