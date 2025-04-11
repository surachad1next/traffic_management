from .database import db
from datetime import datetime

class RobotJobQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_description = db.Column(db.String(255), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=True)
    destination_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('waiting', 'processing', 'completed', 'preempted', 'incompleted', name='job_status'), default='waiting')
    assignedto = db.Column(db.String(100), nullable=True)
    group = db.Column(db.String(100), nullable=True)
    properties = db.Column(db.String(1024), nullable=True)
    parent_job_id = db.Column(db.Integer, db.ForeignKey('robot_job_queue.id'), nullable=True)

    def __repr__(self):
        return f"<JobQueue {self.job_description} - {self.status}>"
