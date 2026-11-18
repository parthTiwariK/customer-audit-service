# Gunicorn + Uvicorn workers for Customer Audit Service.
# From repo root (PYTHONPATH=backend):
#   gunicorn -c deploy/gunicorn.conf.py app.main:app

import multiprocessing
import os

bind = os.environ.get("CASE_AUDIT_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("CASE_AUDIT_WORKERS", min(2, multiprocessing.cpu_count() or 1)))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.environ.get("CASE_AUDIT_TIMEOUT", "120"))
keepalive = 5
accesslog = os.environ.get("CASE_AUDIT_ACCESSLOG", "-")
errorlog = os.environ.get("CASE_AUDIT_ERRORLOG", "-")
loglevel = os.environ.get("CASE_AUDIT_LOG_LEVEL", "info")
preload_app = os.environ.get("CASE_AUDIT_PRELOAD", "false").lower() in ("1", "true", "yes")