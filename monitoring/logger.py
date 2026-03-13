"""
monitoring/logger.py
====================
Configures structured JSON logging writing to rotating files and console.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

import config

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "time": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler (standard formatting for readability)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch_format = logging.Formatter('%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(ch_format)

    # File handler (JSON formatting for log aggregators like ELK)
    fh = RotatingFileHandler(
        config.LOG_FILE, 
        maxBytes=config.LOG_MAX_BYTES, 
        backupCount=config.LOG_BACKUP_COUNT
    )
    fh.setLevel(level)
    fh.setFormatter(JSONFormatter())

    root_logger.addHandler(ch)
    root_logger.addHandler(fh)
    
    # Silence excessively noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
