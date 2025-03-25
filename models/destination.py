from .database import db
import uuid

class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    official_name = db.Column(db.String(255), nullable=True)
    unique_code = db.Column(db.String(50), nullable=False, unique=True, default=lambda: str(uuid.uuid4())[:8])
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Destination {self.name} ({self.unique_code})>"

    @staticmethod
    def generate_unique_code():
        """ สร้างรหัสที่ไม่ซ้ำกันสำหรับจุดหมายปลายทาง """
        while True:
            code = str(uuid.uuid4())[:8]
            if not Destination.query.filter_by(unique_code=code).first():
                return code
