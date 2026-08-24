import logging
import json
from datetime import datetime
import sys

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno
        }
        # Add extra fields if present
        for key in ['agent_id', 'request_id', 'deploy_id', 'script_id']:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)

def setup_logger(name="jocky"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger

logger = setup_logger()