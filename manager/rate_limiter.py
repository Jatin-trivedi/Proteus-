from functools import wraps
from flask import request, jsonify
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        
        with self.lock:
            # Clean old requests
            self.requests[key] = [t for t in self.requests[key] if now - t < window]
            
            if len(self.requests[key]) >= limit:
                return False
            
            self.requests[key].append(now)
            return True

rate_limiter = RateLimiter()

def rate_limit(limit: int = 100, window: int = 60):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Use client IP as key
            key = request.remote_addr
            
            if not rate_limiter.is_allowed(key, limit, window):
                return jsonify({
                    "error": "Rate limit exceeded",
                    "limit": limit,
                    "window": window,
                    "retry_after": window
                }), 429
            
            return f(*args, **kwargs)
        return decorated
    return decorator