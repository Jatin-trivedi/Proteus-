"""
Variable/String Encryption - Encrypts sensitive strings in the code
"""

import base64
import random
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import re
from typing import Dict, Any, Optional

class VariableEncryptor:
    """Encrypts string literals and sensitive data in scripts"""
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._key = None
        self._generate_key()
        
    def _generate_key(self):
        """Generate a new encryption key for each run"""
        # REPLACED os.urandom(16) with deterministic seeded bytes
        salt = self._rng.getrandbits(128).to_bytes(16, 'big')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"jocky_encryption"))
        self._key = key
        self._salt = salt
        self._cipher = Fernet(key)
        
    def encrypt_strings(self, code: str) -> str:
        """
        Find and encrypt all string literals in the code
        """
        # Pattern to find string literals
        # This is simplified - in production you'd use AST parsing
        string_pattern = r'([\'"])(.*?)\1'
        
        def replace_string(match):
            quote = match.group(1)
            content = match.group(2)
            
            # Don't encrypt if it's already encrypted
            if content.startswith('ENC_'):
                return match.group(0)
                
            # Encrypt the string
            encrypted = self._encrypt_string(content)
            
            # REPLACED global random with self._rng
            var_name = f"_decrypt_{self._rng.randint(1000, 9999)}"
            
            # Create decryption code
            decryption_code = (
                f"{var_name} = __import__('base64').b64decode("
                f"__import__('cryptography.fernet').Fernet("
                f"b'{self._key.decode()}').decrypt("
                f"b'{encrypted}')).decode()"
            )
            
            return f'"{var_name}"'  # Return variable instead of string
            
        # Apply encryption to all strings
        encrypted_code = re.sub(string_pattern, replace_string, code)
        
        # Add decryption helper at the top
        helper = self._generate_decryption_helper()
        
        return helper + "\n" + encrypted_code
    
    def _encrypt_string(self, string: str) -> str:
        """Encrypt a single string"""
        encrypted = self._cipher.encrypt(string.encode())
        return base64.b64encode(encrypted).decode()
    
    def _generate_decryption_helper(self) -> str:
        """Generate the decryption helper code to be injected"""
        return f'''
# JOCKY Decryption Helper
import base64
from cryptography.fernet import Fernet

_JOCKY_KEY = b'{self._key.decode()}'
_JOCKY_SALT = b'{base64.b64encode(self._salt).decode()}'

def _jocky_decrypt(encrypted_data):
    try:
        cipher = Fernet(_JOCKY_KEY)
        return cipher.decrypt(base64.b64decode(encrypted_data)).decode()
    except:
        return encrypted_data  # Fallback
'''
    
    def encrypt_variable(self, var_name: str, value: Any) -> str:
        """Encrypt a variable assignment"""
        encoded = self._encrypt_string(str(value))
        return f"{var_name} = _jocky_decrypt('{encoded}')"
    
    def decrypt_value(self, encrypted: str) -> str:
        """Decrypt an encrypted value"""
        try:
            decoded = base64.b64decode(encrypted)
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode()
        except:
            return encrypted