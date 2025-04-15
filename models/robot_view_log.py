from .database import db

class ViewRobotLog(db.Model):
    __tablename__ = 'view_robot_log'  # ชื่อของ view ที่สร้างใน MySQL

    id = db.Column(db.Integer, primary_key=True) 
    robot_id = db.Column(db.String(50))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime)
    details = db.Column(db.String(255))

    def __repr__(self):
        return f"<ViewLog {self.robot_id} - {self.action} - {self.timestamp}>"
    
    def serialize(self):
        return {
            'id': self.id,
            'robot_id': self.robot_id,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }