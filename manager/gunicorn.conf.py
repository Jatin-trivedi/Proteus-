import os

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Keep the default conservative for deployments with limited database connections.
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "100"))
timeout = 120
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Health check
def when_ready(server):
    server.log.info("Gunicorn server ready!")