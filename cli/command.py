import click
from datetime import datetime, timedelta
from models.robot_log import RobotLog
from models.database import db
from flask import current_app

@click.command('clear_old_logs')  # ระบุชื่อคำสั่งที่ต้องการใน CLI
def clear_old_logs():
    db_oldday = int(current_app.config.get("DB_OLD", 7))
    cutoff_date = datetime.utcnow() - timedelta(days=db_oldday)
    old_logs = RobotLog.query.filter(RobotLog.timestamp < cutoff_date).all()

    # บันทึก log ว่ามีการลบ log เก่า
    log_action('system', 'Clear old logs', f"Deleted {len(old_logs)} logs older than {cutoff_date}")
    
    # ลบ log เก่ากว่า db_oldday
    for log in old_logs:
        db.session.delete(log)
    
    db.session.commit()

    print(f"{len(old_logs)} logs have been deleted.")
    return len(old_logs)

# ฟังก์ชันบันทึก Log
def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()