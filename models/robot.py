from .database import db

class Robot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    robot_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    previous_status = db.Column(db.String(20), nullable=True)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    angle = db.Column(db.Float, nullable=False)
    poi = db.Column(db.String(100), nullable=True)
    battery = db.Column(db.Float, nullable=True)
    pickup_id = db.Column(db.Integer)
    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=True)
    properties = db.Column(db.String(1024), nullable=True)

    destination = db.relationship('Destination', backref='robots')

    areas = db.relationship("RobotArea", back_populates="robot", lazy="dynamic")

    def __repr__(self):
        return f"<Robot {self.robot_id}>"
