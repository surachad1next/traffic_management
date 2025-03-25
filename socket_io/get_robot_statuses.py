from flask_socketio import SocketIO, emit
from models.robot import Robot
from models.database import db

def handle_get_robot_statuses(data):
    # ดึงหุ่นยนต์ทั้งหมดจากฐานข้อมูล
    robots = Robot.query.all()
    
    robot_status_list = []

    for robot in robots:
        # ถ้าหุ่นยนต์มี destination, จะส่งข้อมูล destination ด้วย
        destination_data = None
        if robot.destination:
            destination_data = {
                'name': robot.destination.name,
                'x': robot.destination.x,
                'y': robot.destination.y
            }
        
        # เก็บข้อมูลหุ่นยนต์
        robot_status_list.append({
            'robot_id': robot.robot_id,
            'status': robot.status,
            'poi': robot.poi,
            'coordinates': {'x': robot.x, 'y': robot.y,'angle':robot.angle,'poi':robot.poi},
            'heartbeat': {
                'last_seen': str(robot.heartbeat.last_seen) if robot.heartbeat else None,
                'status': robot.heartbeat.status if robot.heartbeat else None,
            },
            'destination': destination_data,
            'properties':robot.properties
        })
    
    # ส่งข้อมูลกลับไปยัง client
    emit('robot_statuses', {'robots': robot_status_list})