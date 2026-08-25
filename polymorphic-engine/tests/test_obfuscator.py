import unittest
import hashlib
from src.obfuscator import PolymorphicEngine

class TestPolymorphicEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = PolymorphicEngine()
        self.test_script = """
import os
import sys

def collect_registry(path):
    data = []
    for key in path:
        result = os.getenv(key)
        if result:
            data.append(result)
    return data

if __name__ == '__main__':
    result = collect_registry(['PATH', 'USERNAME'])
    print(result)
"""
    
    def test_obfuscation_changes_code(self):
        """Test that obfuscation produces different code"""
        result1 = self.engine.obfuscate_script(self.test_script)
        result2 = self.engine.obfuscate_script(self.test_script)
        
        self.assertNotEqual(result1['hash'], result2['hash'])
        self.assertNotEqual(
            result1['obfuscated_code'],
            result2['obfuscated_code']
        )
    
    def test_hash_changes_on_each_run(self):
        """Test that hash changes on every run"""
        hashes = set()
        for _ in range(10):
            result = self.engine.obfuscate_script(self.test_script)
            hashes.add(result['hash'])
        
        # All 10 hashes should be unique
        self.assertEqual(len(hashes), 10)
    
    def test_import_table_obfuscation(self):
        """Test that imports are obfuscated"""
        result = self.engine.obfuscate_script(self.test_script)
        code = result['obfuscated_code']
        
        # Original imports should be obfuscated
        self.assertNotIn('import os', code)
        self.assertNotIn('import sys', code)
    
    def test_obfuscation_increases_size(self):
        """Test that obfuscation increases code size"""
        result = self.engine.obfuscate_script(self.test_script)
        
        self.assertGreater(
            result['obfuscated_size'],
            result['original_size']
        )

if __name__ == '__main__':
    unittest.main()