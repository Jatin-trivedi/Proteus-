import os
import ssl

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

# Gunicorn terminates TLS in production. When mTLS is enabled, only clients
# signed by the configured relay CA can complete the TLS handshake.
if os.getenv("MTLS_REQUIRED", "false").lower() in {"1", "true", "yes", "on"}:
    certfile = os.environ["MTLS_SERVER_CERT"]
    keyfile = os.environ["MTLS_SERVER_KEY"]
    ca_certs = os.environ["MTLS_CLIENT_CA"]
    cert_reqs = ssl.CERT_REQUIRED

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