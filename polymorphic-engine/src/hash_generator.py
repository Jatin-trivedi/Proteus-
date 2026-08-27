"""
Hash Generator - Creates unique identifiers that change every run
"""

import hashlib
import random
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import struct
import os

class HashGenerator:
    """Generates unique hashes that change on every execution"""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize with optional seed for reproducibility"""
        if seed is None:
            # Changed: Use self._rng instead of global random/time
            self._rng = random.Random()
            seed = int(time.time() * 1000) ^ self._rng.randint(0, 2**32)
        else:
            # If seed is provided, use it
            self._rng = random.Random(seed)
            
        self.seed = seed
        # Removed duplicate self._rng assignment
        
    def generate_script_hash(self, script_content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Generate a unique hash for a script that changes every time
        Even for identical scripts, hashes will differ
        """
        if metadata is None:
            metadata = {}
            
        # Add random elements that change every invocation
        # CHANGED: Replaced all unseeded sources with self._rng and self.seed
        unique_elements = [
            str(self.seed),
            str(int(time.time() * 1000)), # Note: time.time is still unseeded, but for the 'marker' logic it's okay because we want it to change. However, to make it deterministic for the test, we MUST replace it.
            # We will replace time.time() with a value from self._rng
        ]
        
        # FULLY REPLACED unique_elements to be deterministic
        unique_elements = [
            str(self.seed),
            str(self._rng.randint(0, 10**9)), # Replaces time.time() * 1000
            str(self._rng.getrandbits(128)),  # Replaces uuid.uuid4()
            str(self._rng.randint(0, 10**9)), # Replaces random.randint(0, 10**9)
            str(self._rng.randint(0, 100000)), # Replaces os.getpid()
            str(self._rng.randint(0, 999999)) # Replaces datetime.now().microsecond
        ]
        
        # Combine with script content and metadata
        combined = script_content + "|".join(unique_elements)
        for key, value in metadata.items():
            combined += f"|{key}:{value}"
            
        # Generate multiple hash types
        md5_hash = hashlib.md5(combined.encode('utf-8')).hexdigest()
        sha256_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        # Add some custom hash modifications
        # This makes it harder for signature detection
        custom_hash = self._custom_hash(combined)
        
        return {
            'md5': md5_hash,
            'sha256': sha256_hash,
            'custom': custom_hash,
            'timestamp': datetime.now().isoformat()
        }
    
    def _custom_hash(self, data: str) -> str:
        """Create a custom hash algorithm to avoid standard signatures"""
        # Modified hash algorithm
        hash_val = 0
        for i, char in enumerate(data):
            # Use prime numbers and bit operations
            hash_val = ((hash_val << 7) ^ (hash_val >> 3)) ^ ord(char)
            hash_val = (hash_val * 3141592653) & 0xFFFFFFFF
            # Add some chaos
            if i % 3 == 0:
                hash_val ^= 0xDEADBEEF
            if i % 5 == 0:
                hash_val = (hash_val << 1) | (hash_val >> 31)
        return format(hash_val, '08x')
    
    def generate_file_hash(self, file_data: bytes) -> Dict[str, str]:
        """Generate hashes for binary files"""
        import hashlib
        
        # Add random padding that changes each time
        # CHANGED: Replaced os.urandom(16) with self._rng
        padding = self._rng.getrandbits(128).to_bytes(16, 'big')
        padded_data = file_data + padding
        
        hashes = {
            'md5': hashlib.md5(padded_data).hexdigest(),
            'sha1': hashlib.sha1(padded_data).hexdigest(),
            'sha256': hashlib.sha256(padded_data).hexdigest(),
        }
        
        # Also generate a custom checksum
        hashes['custom'] = self._generate_checksum(file_data)
        
        return hashes
    
    def _generate_checksum(self, data: bytes) -> str:
        """Generate custom checksum that changes per run"""
        import zlib
        # Combine multiple algorithms with random factors
        crc = zlib.crc32(data) & 0xFFFFFFFF
        adler = zlib.adler32(data) & 0xFFFFFFFF
        # Add random seed from this instance
        combined = f"{crc:x}{adler:x}{self.seed:x}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def mutate_identifier(self, identifier: str) -> str:
        """Mutate any identifier to a different but functionally equivalent one"""
        mutators = [
            lambda s: s[::-1],
            lambda s: s + str(self._rng.randint(0, 999)), # CHANGED: random -> self._rng
            lambda s: self._leet_speak(s),
            lambda s: s.upper() + str(self._rng.randint(0, 99)), # CHANGED: random -> self._rng
            lambda s: self._reverse_capitalize(s),
            lambda s: hashlib.md5(s.encode()).hexdigest()[:8]
        ]
        
        mutator = self._rng.choice(mutators) # CHANGED: random.choice -> self._rng.choice
        return mutator(identifier)
    
    def _leet_speak(self, text: str) -> str:
        """Convert text to leet speak"""
        leet_map = {
            'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5',
            't': '7', 'b': '8', 'g': '9', 'z': '2'
        }
        return ''.join(leet_map.get(c.lower(), c) for c in text)
    
    def _reverse_capitalize(self, text: str) -> str:
        """Reverse capitalization pattern"""
        result = []
        for i, char in enumerate(text):
            if i % 2 == 0:
                result.append(char.upper() if char.islower() else char.lower())
            else:
                result.append(char)
        return ''.join(result)