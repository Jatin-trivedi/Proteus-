"""
Import Table Obfuscator - Hides API calls from static analysis
"""

import random
import struct
from typing import Dict, Any, Optional, List, Tuple
import re

class ImportTableObfuscator:
    """
    Obfuscates import tables and API calls
    Makes it harder for static analysis to determine what functions are used
    """
    
    def __init__(self):
        self._rng = random.Random()
        self._api_resolver = None
        
    def obfuscate_imports(self, binary_data: bytes) -> bytes:
        """
        Obfuscate the import table in a PE binary
        """
        # Check if it's a PE file
        if not self._is_pe(binary_data):
            return binary_data
            
        # Parse PE structure (simplified)
        # In production, use pefile library
        try:
            import pefile
            pe = pefile.PE(data=binary_data)
            
            # Modify import table
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    # Obfuscate DLL names
                    entry.dll = self._obfuscate_string(entry.dll)
                    
                    # Obfuscate function names
                    for imp in entry.imports:
                        if imp.name:
                            imp.name = self._obfuscate_string(imp.name)
                            
            # Save modified binary
            return pe.write()
            
        except ImportError:
            # If pefile not available, fallback to basic obfuscation
            return self._basic_obfuscation(binary_data)
        except:
            return binary_data
    
    def _is_pe(self, data: bytes) -> bool:
        """Check if data is a PE file"""
        return data[:2] == b'MZ' and b'PE' in data[:64]
    
    def _obfuscate_string(self, string: str) -> str:
        """Obfuscate a string by adding random characters"""
        if not string:
            return string
            
        # Add random prefix/suffix
        prefix = ''.join(chr(self._rng.randint(65, 90)) for _ in range(3))
        suffix = ''.join(chr(self._rng.randint(48, 57)) for _ in range(3))
        
        # Rotate characters
        rotated = ''.join(
            chr(ord(c) ^ self._rng.randint(1, 255)) 
            for c in string
        )
        
        # Encode
        import base64
        encoded = base64.b64encode(rotated.encode()).decode()
        
        return f"{prefix}{encoded}{suffix}"
    
    def _basic_obfuscation(self, data: bytes) -> bytes:
        """Basic obfuscation when pefile is not available"""
        # Just add some random data to the end
        import os
        random_data = os.urandom(256)
        return data + random_data
    
    def obfuscate_api_call(self, api_name: str) -> str:
        """Obfuscate a single API call"""
        # Split into module and function
        if '.' in api_name:
            module, function = api_name.split('.', 1)
        else:
            module = 'kernel32'
            function = api_name
            
        # Create a resolver function
        resolver = f"_resolve_{self._rng.randint(1000,9999)}"
        
        # Create obfuscated call
        obfuscated = f'''
{resolver} = lambda x: getattr(__import__("{module}"), x)
result = {resolver}("{function}")
'''
        return obfuscated
    
    def generate_resolver_code(self) -> str:
        """Generate code for dynamic API resolution"""
        modules = [
            'kernel32', 'ntdll', 'user32', 'advapi32',
            'ws2_32', 'shell32', 'ole32', 'comctl32'
        ]
        
        # Randomly select modules
        selected = self._rng.sample(modules, self._rng.randint(3, len(modules)))
        
        code = []
        code.append("# JOCKY API Resolver")
        
        for module in selected:
            var_name = f"_{module.replace('32', '').replace('_', '')}_{self._rng.randint(100,999)}"
            code.append(f"{var_name} = __import__('{module}')")
            
        return '\n'.join(code)
    
    def obfuscate_import_statement(self, statement: str) -> str:
        """Obfuscate an import statement"""
        # Randomize the import style
        styles = [
            lambda s: f"__import__('{s}')",
            lambda s: f"import {s} as _{self._rng.randint(1000,9999)}",
            lambda s: f"from {s} import *",
            lambda s: f"# {s}\nimport {s}",
        ]
        
        style = self._rng.choice(styles)
        return style(statement)