from flask_socketio import SocketIO, emit
from models.robot import Robot
from models.robot_area import RobotArea
from models.robot_log import RobotLog
from models.database import db
import time


# Global variables
last_logged_time = 0
LOG_INTERVAL = 60  # Set your log interval in seconds


def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

# @socketio.on('update_coordinates')
def handle_update_coordinates(data):
    global last_logged_time
    robot_id = data.get('robot_id')
    x = data.get('x')
    y = data.get('y')
    angle = data.get('angle')
    poi = data.get('poi')
    battery = data.get('battery')
    area = data.get('area', [])
    
    robot = Robot.query.filter_by(robot_id=robot_id).first()
    if robot:
        previous_coordinates = (robot.x, robot.y)

        # อัพเดทพิกัดหุ่นยนต์
        robot.x = x
        robot.y = y
        robot.angle = angle
        robot.poi = poi
        robot.battery = battery
        db.session.commit()

        if area:
            area_robot = RobotArea.query.filter_by(robot_id=robot.robot_id).first()
            if area == "free":
                if area_robot:
                    db.session.delete(area_robot)
                    db.session.commit()
                    area_robot = None
            else:
                if area_robot:
                    area_robot.set_area_name(area)
                    area_robot.coordinates = data.get('coordinates', area_robot.coordinates)
                    db.session.commit()
                else:
                    new_area = RobotArea(
                        robot_id=robot.robot_id,
                        coordinates='{"posGroup":[{"x":1.131,"y":-0.31},{"x":1.131,"y":0.763},{"x":-0.223,"y":0.763},{"x":-0.223,"y":-0.31}]}'
                    )
                    new_area.set_area_name(area)
                    db.session.add(new_area)
                    db.session.commit()

        # ส่งกลับการอัพเดทข้อมูลหุ่นยนต์
        emit('coordinates_updated', {
            'robot_id': robot.robot_id,
            'coordinates': {'x': robot.x, 'y': robot.y, 'angle': robot.angle, 'poi': robot.poi},
            'message': 'Coordinates updated successfully'
        })

        current_time = time.time()
        if current_time - last_logged_time >= LOG_INTERVAL:
            # หากเกินเวลา interval, บันทึก log
            log_action(robot_id, 'Updated coordinates', f"From {previous_coordinates} to ({robot.x}, {robot.y} , {robot.angle})")
            last_logged_time = current_time  # อัพเดทเวลาที่บันทึก log ล่าสุด
    else:
        emit('error', {'message': 'Robot not found'})
