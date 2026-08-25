import platform
import os
import sys
import time
import random
import hashlib
from typing import Dict

class AntiAnalysis:
    """
    Detect and evade analysis environments:
    - Debugger detection
    - VM detection
    - Sandbox detection
    - Time-based evasion
    """
    
    def __init__(self):
        self.checks = []
        self._initialize_checks()
    
    def _initialize_checks(self):
        """Initialize detection checks"""
        self.checks = [
            self._check_debugger,
            self._check_vm,
            self._check_sandbox,
            self._check_analysis_tools
        ]
    
    def detect_analysis(self) -> Dict[str, bool]:
        """Run all detection checks"""
        results = {}
        for check in self.checks:
            name, detected = check()
            results[name] = detected
        return results
    
    def _check_debugger(self):
        """Check for debugger presence"""
        detected = False
        
        # Check for debugger on Windows
        if platform.system() == 'Windows':
            try:
                import ctypes
                # Check for debugger via IsDebuggerPresent
                kernel32 = ctypes.windll.kernel32
                if kernel32.IsDebuggerPresent():
                    detected = True
            except:
                pass
        
        # Check for common debugger environment variables
        debug_vars = ['DEBUG', 'PYTHONDEBUG', 'PYCHARM_HOSTED']
        for var in debug_vars:
            if os.environ.get(var):
                detected = True
                break
        
        return 'debugger_detected', detected
    
    def _check_vm(self):
        """Check for virtual machine presence"""
        detected = False
        
        # Check common VM indicators
        vm_indicators = [
            'VBOX', 'VMWARE', 'VIRTUAL', 'QEMU', 'XEN'
        ]
        
        # Check system info
        if platform.system() == 'Windows':
            try:
                import wmi
                c = wmi.WMI()
                for item in c.Win32_ComputerSystem():
                    for indicator in vm_indicators:
                        if indicator in item.Model:
                            detected = True
                            break
            except:
                pass
        
        # Check for VM-specific devices
        try:
            if os.path.exists('/dev/vboxguest'):
                detected = True
            if os.path.exists('/dev/xen'):
                detected = True
        except:
            pass
        
        return 'vm_detected', detected
    
    def _check_sandbox(self):
        """Check for sandbox environment"""
        detected = False
        
        # Check for analysis tools
        sandbox_indicators = ['CUCKOO', 'SANDBOX', 'ANALYSIS']
        
        for indicator in sandbox_indicators:
            for var in os.environ:
                if indicator in var.upper():
                    detected = True
                    break
        
        # Check for small RAM (common in sandboxes)
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.total < 2 * 1024 * 1024 * 1024:  # Less than 2GB
                detected = True
        except:
            pass
        
        return 'sandbox_detected', detected
    
    def _check_analysis_tools(self):
        """Check for analysis tools running"""
        detected = False
        
        # Common analysis tools
        analysis_tools = [
            'PROCMON', 'WIRESHARK', 'TCPDUMP', 'OLYDBG', 'IDA',
            'GHIDRA', 'RADARE2', 'BURPSUITE'
        ]
        
        # Check running processes (simplified)
        try:
            import psutil
            for proc in psutil.process_iter():
                try:
                    name = proc.name().upper()
                    for tool in analysis_tools:
                        if tool in name:
                            detected = True
                            break
                except:
                    pass
        except:
            pass
        
        return 'analysis_tools_detected', detected
    
    def execute_with_evasion(self, func, *args, **kwargs):
        """Execute a function with evasion checks"""
        # Add random delay to avoid time-based detection
        time.sleep(random.uniform(0.1, 0.5))
        
        # Run detection
        results = self.detect_analysis()
        
        # If analysis detected, execute with evasion
        if any(results.values()):
            print("[!] Analysis environment detected! Using evasion...")
            # Use anti-debug techniques
            self._anti_debug()
            # Execute with random delays
            time.sleep(random.uniform(1, 3))
        
        return func(*args, **kwargs)
    
    def _anti_debug(self):
        """Anti-debugging techniques"""
        # Generate random exceptions (harmless)
        try:
            raise Exception("Random exception for evasion")
        except:
            pass
        
        # Mask API calls (simplified)
        if platform.system() == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # Call with random delays
                kernel32.Sleep(random.randint(100, 500))
            except:
                pass