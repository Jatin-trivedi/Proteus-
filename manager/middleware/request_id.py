from flask import request, g
import uuid
import time

class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        # Generate request ID
        request_id = environ.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        environ['REQUEST_ID'] = request_id
        
        # Store start time
        environ['START_TIME'] = time.time()
        
        return self.app(environ, start_response)