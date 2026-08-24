import hashlib
import json
import os
from datetime import datetime

class CompilerCache:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()
    
    def get(self, source: str):
        key = self.get_cache_key(source)
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                print(f"✅ Cache hit for key: {key[:16]}...")
                return data
        return None
    
    def set(self, source: str, ast_data: dict):
        key = self.get_cache_key(source)
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        with open(cache_file, 'w') as f:
            json.dump({
                "ast": ast_data,
                "cached_at": datetime.utcnow().isoformat(),
                "key": key
            }, f)
        print(f"✅ Cached for key: {key[:16]}...")
    
    def clear(self):
        """Clear all cache"""
        import shutil
        shutil.rmtree(self.cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        print("🧹 Cache cleared")

compiler_cache = CompilerCache()