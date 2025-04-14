from flask_restful import Resource, reqparse
from models.robot_log import RobotLog
from models.robot import Robot
from models.database import db

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class AvailableRobots(Resource):
    def get(self):
        # ดึงหุ่นยนต์ที่มีสถานะเป็น 'available'
        available_robots = Robot.query.all()
        robots_list = [{'robot_id': robot.robot_id} for robot in available_robots]
        return robots_list, 200

    def post(self):
        # การเพิ่มหุ่นยนต์ใหม่ พร้อมพิกัด x และ y
        parser = reqparse.RequestParser()
        parser.add_argument('robot_id', type=str, required=True, help="Robot ID cannot be blank")
        parser.add_argument('x', type=float, required=True, help="X coordinate cannot be blank")
        parser.add_argument('y', type=float, required=True, help="Y coordinate cannot be blank")
        parser.add_argument('angle', type=float, required=True, help="angle coordinate cannot be blank")
        args = parser.parse_args()

        # ตรวจสอบว่ามีหุ่นยนต์ที่มี robot_id นี้อยู่แล้วหรือไม่
        if Robot.query.filter_by(robot_id=args['robot_id']).first():
            return {'message': 'Robot with this ID already exists'}, 400

        # เพิ่มหุ่นยนต์ใหม่
        new_robot = Robot(robot_id=args['robot_id'], x=args['x'], y=args['y'], angle=args['angle'])
        db.session.add(new_robot)
        db.session.commit()

        # บันทึก log การเพิ่มหุ่นยนต์
        log_action(args['robot_id'], 'Robot added')

        return {'message': 'Robot added', 'robot_id': new_robot.robot_id, 'x': new_robot.x, 'y': new_robot.y,'angle':new_robot.angle}, 201