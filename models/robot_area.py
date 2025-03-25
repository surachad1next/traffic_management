from .database import db
from datetime import datetime
import json

class RobotArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50), db.ForeignKey('robot.robot_id'), nullable=False)
    area_name = db.Column(db.Text, nullable=False)
    coordinates = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    robot = db.relationship("Robot", back_populates="areas")

    def __repr__(self):
        return f"<RobotArea {self.area_name} for Robot {self.robot_id}>"

    def set_area_name(self, area_list):
        """แปลง list เป็น JSON string"""
        self.area_name = json.dumps(area_list)

    def get_area_name(self):
        """แปลง JSON string กลับเป็น list"""
        return json.loads(self.area_name)
