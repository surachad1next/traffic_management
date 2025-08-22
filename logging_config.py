import logging
import sys
from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name="app", logfile="sys.log"):
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

        # ✅ หมุนไฟล์ทุกวัน เวลาเที่ยงคืน เก็บย้อนหลัง 7 วัน
        file_handler = TimedRotatingFileHandler(
            logfile, when="midnight", interval=1, backupCount=7, encoding="utf-8"
        )
        # file_handler = RotatingFileHandler(
        #     logfile, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        # )
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger
