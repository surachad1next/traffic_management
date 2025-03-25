from .database import db
from datetime import datetime

class Heartbeat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.Integer, db.ForeignKey('robot.id'), nullable=False, unique=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='active')

    robot = db.relationship('Robot', backref=db.backref('heartbeat', uselist=False))


    def __repr__(self):
        return f"<Heartbeat for Robot {self.robot_id} - Last Seen: {self.last_seen}>"
