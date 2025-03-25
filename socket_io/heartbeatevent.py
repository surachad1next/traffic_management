from flask_socketio import SocketIO, emit
from models.robot import Robot
from models.database import db
from models.heartbeat import Heartbeat
from datetime import datetime


def handle_heartbeat(data):
    robot_id = data.get('robot_id')
    # print(robot_id)
    if not robot_id:
        emit('error', {'message': 'Robot ID is missing', 'code': 400})
        return

    # ค้นหา Robot
    robot = Robot.query.filter_by(robot_id=robot_id).first()
    if not robot:
        emit('error', {'message': 'Robot not found', 'code': 404})
        return

    # อัปเดตหรือเพิ่ม heartbeat
    heartbeat = Heartbeat.query.filter_by(robot_id=robot.id).first()
    if heartbeat:
        heartbeat.last_seen = datetime.utcnow()
        heartbeat.status = 'active'
    else:
        heartbeat = Heartbeat(robot_id=robot.id, last_seen=datetime.utcnow(), status='active')
        db.session.add(heartbeat)
    # print(heartbeat)
    db.session.commit()

    emit('heartbeat_ack', {'message': f'Heartbeat received from robot {robot_id}', 'code': 200})