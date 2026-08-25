import random
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class VariableEncryptor:
    """Encrypt strings and variable names to avoid pattern matching"""
    
    def __init__(self):
        # Generate random key for this session
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
        # Common variable names to replace
        self.common_names = [
            'data', 'result', 'temp', 'value', 'count',
            'index', 'item', 'flag', 'status', 'buffer'
        ]
    
    def encrypt_strings(self, code: str) -> str:
        """Encrypt string literals and replace with decryption calls"""
        lines = code.split('\n')
        encrypted_lines = []
        
        for line in lines:
            # Find strings in quotes
            if '"' in line or "'" in line:
                line = self._encrypt_string_in_line(line)
            encrypted_lines.append(line)
        
        # Add decryption helper at the top
        helper = self._generate_decryption_helper()
        return helper + '\n'.join(encrypted_lines)
    
    def _encrypt_string_in_line(self, line: str) -> str:
        """Encrypt a single string literal"""
        import re
        
        # Pattern to match quoted strings
        pattern = r'["\']([^"\']*)["\']'
        
        def encrypt_match(match):
            original = match.group(1)
            if len(original) > 3:  # Don't encrypt short strings
                encrypted = self._encrypt_string(original)
                return f'_decrypt("{encrypted}")'
            return match.group(0)
        
        return re.sub(pattern, encrypt_match, line)
    
    def _encrypt_string(self, text: str) -> str:
        """Encrypt a string and return base64"""
        encrypted = self.cipher.encrypt(text.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_string(self, encrypted: str) -> str:
        """Decrypt a string (used at runtime)"""
        decrypted = self.cipher.decrypt(base64.b64decode(encrypted))
        return decrypted.decode()
    
    def _generate_decryption_helper(self) -> str:
        """Generate unique decryption helper function"""
        func_name = f'_decrypt_{random.randint(1000, 9999)}'
        
        return f'''
# Dynamic decryption helper
def {func_name}(encrypted_data):
    import base64
    from cryptography.fernet import Fernet
    key = b'{self.key.decode()}'
    cipher = Fernet(key)
    decrypted = cipher.decrypt(base64.b64decode(encrypted_data))
    return decrypted.decode()

'''