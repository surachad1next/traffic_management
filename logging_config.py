import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name="app", logfile="sys.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    file_handler = RotatingFileHandler(logfile, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger