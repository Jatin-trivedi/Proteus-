import random
import base64
import hashlib
from typing import List, Tuple

class StringObfuscator:
    """
    Advanced string obfuscation:
    - Split strings into multiple parts
    - XOR encryption
    - Dynamic construction
    - Environment variable lookup
    """
    
    def __init__(self):
        self.key = random.randint(1, 255)
        
    def obfuscate_strings(self, code: str) -> str:
        """Obfuscate all string literals in the code"""
        lines = code.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            if '"' in line or "'" in line:
                line = self._process_strings(line)
            obfuscated_lines.append(line)
        
        # Add string reconstruction helpers
        helpers = self._generate_helpers()
        return helpers + '\n' + '\n'.join(obfuscated_lines)
    
    def _process_strings(self, line: str) -> str:
        """Process a line containing strings"""
        import re
        
        def replace_string(match):
            original = match.group(1)
            if len(original) > 2:
                return self._obfuscate_single_string(original)
            return match.group(0)
        
        # Match strings in quotes
        pattern = r'["\']([^"\']*)["\']'
        return re.sub(pattern, replace_string, line)
    
    def _obfuscate_single_string(self, text: str) -> str:
        """Obfuscate a single string using multiple techniques"""
        technique = random.choice(['split', 'xor', 'base64', 'reverse'])
        
        if technique == 'split':
            return self._split_string(text)
        elif technique == 'xor':
            return self._xor_encrypt(text)
        elif technique == 'base64':
            return self._base64_obfuscate(text)
        else:
            return self._reverse_string(text)
    
    def _split_string(self, text: str) -> str:
        """Split string into multiple parts"""
        if len(text) < 3:
            return f'"{text}"'
        
        # Split into random parts
        parts = []
        remaining = text
        while len(remaining) > 2:
            split_point = random.randint(1, min(5, len(remaining)-1))
            parts.append(remaining[:split_point])
            remaining = remaining[split_point:]
        if remaining:
            parts.append(remaining)
        
        # Return as concatenated parts
        return ' + '.join([f'"{part}"' for part in parts])
    
    def _xor_encrypt(self, text: str) -> str:
        """XOR encrypt the string"""
        encrypted = ''.join([chr(ord(c) ^ self.key) for c in text])
        return f'_xor_decrypt("{base64.b64encode(encrypted.encode()).decode()}")'
    
    def _base64_obfuscate(self, text: str) -> str:
        """Base64 encode the string"""
        encoded = base64.b64encode(text.encode()).decode()
        return f'_b64_decode("{encoded}")'
    
    def _reverse_string(self, text: str) -> str:
        """Reverse the string"""
        reversed_text = text[::-1]
        return f'_reverse("{reversed_text}")'
    
    def _generate_helpers(self) -> str:
        """Generate helper functions for string reconstruction"""
        return f'''
# String reconstruction helpers
def _xor_decrypt(data):
    import base64
    key = {self.key}
    decrypted = base64.b64decode(data).decode()
    return ''.join([chr(ord(c) ^ key) for c in decrypted])

def _b64_decode(data):
    import base64
    return base64.b64decode(data).decode()

def _reverse(data):
    return data[::-1]
'''