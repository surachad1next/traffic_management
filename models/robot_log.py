from .database import db
from datetime import datetime

class RobotLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Log {self.robot_id} - {self.action} - {self.timestamp}>"
