import json
import logging
import time
from flask import request, g

class LoggingMiddleware:
    def __init__(self, app, logger=None):
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
    
    def __call__(self, environ, start_response):
        # Get request ID from environment
        request_id = environ.get('REQUEST_ID', 'unknown')
        start_time = environ.get('START_TIME', time.time())
        
        # Log request
        self.logger.info(
            f"Request started",
            extra={
                'request_id': request_id,
                'method': environ.get('REQUEST_METHOD'),
                'path': environ.get('PATH_INFO'),
                'remote_addr': environ.get('REMOTE_ADDR')
            }
        )
        
        # Process request
        def custom_start_response(status, headers, exc_info=None):
            # Add request ID to response headers
            headers.append(('X-Request-ID', request_id))
            headers.append(('X-Response-Time', f"{time.time() - start_time:.3f}s"))
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)