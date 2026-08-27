"""
Unit tests for the polymorphic engine
"""

import unittest
import tempfile
import os
import sys
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.obfuscator import PolymorphicObfuscator
from src.hash_generator import HashGenerator
from src.variable_encryption import VariableEncryptor
from src.junk_code_injector import JunkCodeInjector

class TestPolymorphicEngine(unittest.TestCase):
    
    def setUp(self):
        self.obfuscator = PolymorphicObfuscator(seed=42)
        self.test_script = '''
def collect_registry(path):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    values = []
    i = 0
    while True:
        try:
            name, value, _ = winreg.EnumValue(key, i)
            values.append({name: value})
            i += 1
        except WindowsError:
            break
    winreg.CloseKey(key)
    return values

def main():
    result = collect_registry("SOFTWARE\\Microsoft\\Windows\\CurrentVersion")
    print("Registry data:", result)
    
if __name__ == "__main__":
    main()
'''
    
    def test_hash_generation_different(self):
        """Test that hashes are different on each run"""
        hash_gen1 = HashGenerator()
        hash_gen2 = HashGenerator()
        
        hash1 = hash_gen1.generate_script_hash(self.test_script)
        hash2 = hash_gen2.generate_script_hash(self.test_script)
        
        self.assertNotEqual(hash1['md5'], hash2['md5'])
        self.assertNotEqual(hash1['sha256'], hash2['sha256'])
        
    def test_obfuscation_changes_code(self):
        """Test that obfuscation changes the code"""
        result = self.obfuscator.obfuscate_script(self.test_script)
        obfuscated = result['obfuscated_script']
        
        # Code should be different
        self.assertNotEqual(self.test_script, obfuscated)
        
        # Should have junk code injected
        self.assertTrue('_junk_' in obfuscated or 'JOCKY' in obfuscated)
        
        # Should have unique hashes
        self.assertIsNotNone(result['hashes'])
        self.assertTrue('md5' in result['hashes'])
        self.assertTrue('sha256' in result['hashes'])
        
    def test_multiple_obfuscations_different(self):
        """Test that multiple obfuscations produce different results"""
        result1 = self.obfuscator.obfuscate_script(self.test_script)
        result2 = self.obfuscator.obfuscate_script(self.test_script)
        
        self.assertNotEqual(
            result1['obfuscated_script'],
            result2['obfuscated_script']
        )
        
    def test_junk_code_injection(self):
        """Test junk code injection"""
        injector = JunkCodeInjector()
        modified = injector.inject_junk_code(self.test_script)
        
        # Should contain junk code
        self.assertTrue('_junk_' in modified or 'JOCKY' in modified)
        
        # Original code should still be intact
        self.assertTrue('def collect_registry' in modified)
        self.assertTrue('def main()' in modified)
        
    def test_variable_encryption(self):
        """Test string encryption"""
        encryptor = VariableEncryptor()
        encrypted = encryptor.encrypt_strings(self.test_script)
        
        # Should contain encryption helpers
        self.assertTrue('_jocky_decrypt' in encrypted)
        self.assertTrue('Fernet' in encrypted)
        
        # Original strings should be encrypted
        self.assertFalse('"SOFTWARE\\Microsoft' in encrypted)
        
    def test_file_hash_changes(self):
        """Test that file hashes change"""
        hash_gen = HashGenerator()
        
        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
            
        try:
            hash1 = hash_gen.generate_file_hash(b"test data")
            
            # Small change to data
            hash2 = hash_gen.generate_file_hash(b"test data1")
            
            self.assertNotEqual(hash1['md5'], hash2['md5'])
            self.assertNotEqual(hash1['sha256'], hash2['sha256'])
            
        finally:
            os.unlink(temp_path)
            
    def test_obfuscation_with_seed(self):
        """Test that same seed produces same results"""
        obf1 = PolymorphicObfuscator(seed=123)
        obf2 = PolymorphicObfuscator(seed=123)
        
        result1 = obf1.obfuscate_script(self.test_script)
        result2 = obf2.obfuscate_script(self.test_script)
        
        self.assertEqual(
            result1['obfuscated_script'],
            result2['obfuscated_script']
        )

if __name__ == '__main__':
    unittest.main()