import hashlib
import random
import time

class HashGenerator:
    """Generate unique hashes for each deployment"""
    
    def generate(self, code: str, seed: int) -> str:
        """Generate unique hash for the obfuscated code"""
        # Add randomness to the hash
        salt = str(random.randint(100000, 999999))
        timestamp = str(int(time.time()))
        
        # Combine code with random elements
        combined = code + salt + timestamp + str(seed)
        
        # Generate multiple hashes
        md5_hash = hashlib.md5(combined.encode()).hexdigest()
        sha256_hash = hashlib.sha256(combined.encode()).hexdigest()
        sha1_hash = hashlib.sha1(combined.encode()).hexdigest()
        
        # Create a composite hash with random selection
        hash_components = [md5_hash, sha256_hash, sha1_hash]
        selected = random.choice(hash_components)
        
        # Add random prefix/suffix
        prefix = ''.join(random.choices('abcdef0123456789', k=4))
        suffix = ''.join(random.choices('abcdef0123456789', k=4))
        
        return f"{prefix}_{selected}_{suffix}"