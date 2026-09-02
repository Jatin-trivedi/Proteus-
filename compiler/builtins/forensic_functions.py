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

def get_open_windows() -> str:
    windows = []
    sys_name = platform.system()
    if sys_name == "Windows":
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            
            def enum_windows_callback(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        class_buff = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_buff, 256)
                        windows.append({
                            "hwnd": hwnd,
                            "title": buff.value,
                            "class": class_buff.value
                        })
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
            return json.dumps(windows)
        except Exception as e:
            return json.dumps([{"error": str(e)}])
    elif sys_name == "Darwin":
        try:
            # 1. Get running GUI applications
            app_cmd = "osascript -e 'tell application \"System Events\" to get name of every process whose background only is false'"
            res = subprocess.run(app_cmd, shell=True, capture_output=True, text=True, timeout=3)
            if res.stdout:
                apps = [a.strip() for a in res.stdout.replace("\n", "").split(",") if a.strip()]
                for app_name in apps:
                    windows.append({"app": app_name, "type": "GUI Application Window", "platform": "macOS"})
            
            # 2. Extract active browser tabs if Chrome / Safari is running
            try:
                chrome_cmd = "osascript -e 'if application \"Google Chrome\" is running then tell application \"Google Chrome\" to get title of every tab of every window'"
                c_res = subprocess.run(chrome_cmd, shell=True, capture_output=True, text=True, timeout=2)
                if c_res.stdout:
                    c_tabs = [t.strip() for t in c_res.stdout.replace("\n", "").split(",") if t.strip()]
                    for tab in c_tabs:
                        windows.append({"title": tab, "app": "Google Chrome", "type": "Browser Tab"})
            except Exception:
                pass
            
            if not windows:
                windows.append({"title": "Finder / Desktop Session", "platform": "macOS"})
            return json.dumps(windows)
        except Exception as e:
            return json.dumps([{"error": str(e)}])
    else:
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.strip().splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    windows.append({"hwnd": parts[0], "desktop": parts[1], "host": parts[2], "title": parts[3]})
            return json.dumps(windows)
        except Exception as e:
            return json.dumps([{"error": str(e)}])

def pack(*args) -> str:
    return json.dumps({
        'results': args,
        'count': len(args)
    })

def print_msg(msg: str) -> None:
    print(msg)