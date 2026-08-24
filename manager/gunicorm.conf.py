import multiprocessing
import os

# Server
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 120
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Health check
def when_ready(server):
    server.log.info("Gunicorn server ready!")