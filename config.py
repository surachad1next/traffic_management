import os
from dotenv import load_dotenv
from sqlalchemy.pool import QueuePool
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': QueuePool,
        'pool_pre_ping': True,
        'pool_size': 10,           # จำนวน connection หลัก
        'max_overflow': 20,        # จำนวน connection เพิ่มได้เกินจาก pool_size
        'pool_timeout': 30,        # รอเชื่อมต่อนานแค่ไหนก่อน timeout
        'pool_recycle': 280       # รีไซเคิล connection ทุก 30 นาที
    }
    DB_OLD = int(os.getenv("DB_OLD", 7))