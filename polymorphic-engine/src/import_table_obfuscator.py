import random
import re
from typing import List, Tuple

class ImportTableObfuscator:
    """Hide API imports to avoid signature matching"""
    
    # Common Windows APIs used in forensics
    WINDOWS_APIS = [
        'CreateProcess', 'VirtualAllocEx', 'WriteProcessMemory',
        'CreateRemoteThread', 'GetProcAddress', 'LoadLibrary',
        'NtCreateProcess', 'NtAllocateVirtualMemory', 'ZwWriteVirtualMemory'
    ]
    
    # Linux syscalls
    LINUX_SYSCALLS = [
        'syscall.SYS_execve', 'syscall.SYS_mmap', 'syscall.SYS_ptrace',
        'syscall.SYS_process_vm_writev', 'syscall.SYS_openat'
    ]
    
    def obfuscate(self, code: str) -> Tuple[str, List[str]]:
        """Obfuscate import statements and return import table"""
        import_table = []
        
        # Detect imports and obfuscate them
        lines = code.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            if 'import ' in line or 'from ' in line:
                # Extract imported modules/functions
                imported = self._extract_imports(line)
                import_table.extend(imported)
                
                # Obfuscate the import
                line = self._obfuscate_import_line(line)
            
            obfuscated_lines.append(line)
        
        return '\n'.join(obfuscated_lines), import_table
    
    def _extract_imports(self, line: str) -> List[str]:
        """Extract imported names from import statement"""
        imports = []
        # Simple extraction - get everything after 'import'
        if 'import ' in line:
            parts = line.split('import')
            if len(parts) > 1:
                items = parts[1].split(',')
                for item in items:
                    imports.append(item.strip())
        return imports
    
    def _obfuscate_import_line(self, line: str) -> str:
        """Transform import into dynamic loading"""
        import_names = re.findall(r'import\s+(\w+)', line)
        
        if not import_names:
            return line
        
        # Replace with dynamic import
        dynamic_imports = []
        for name in import_names:
            dynamic_imports.append(f"globals()['{name}'] = __import__('{name}')")
        
        return '; '.join(dynamic_imports)