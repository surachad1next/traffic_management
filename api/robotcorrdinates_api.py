from flask_restful import Resource, reqparse
from models.robot_log import RobotLog
from models.robot import Robot
from models.database import db

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()
    
class RobotCoordinates(Resource):
    def put(self, robot_id):
        # อัพเดทพิกัดของหุ่นยนต์
        parser = reqparse.RequestParser()
        parser.add_argument('x', type=float, required=True, help="X coordinate cannot be blank")
        parser.add_argument('y', type=float, required=True, help="Y coordinate cannot be blank")
        parser.add_argument('angle', type=float, required=True, help="angle coordinate cannot be blank")
        args = parser.parse_args()

        robot = Robot.query.filter_by(robot_id=robot_id).first()
        if robot:
            previous_coordinates = (robot.x, robot.y)

            # อัพเดทพิกัด
            robot.x = args['x']
            robot.y = args['y']
            robot.angle = args['angle']

            db.session.commit()

            # บันทึก log การเปลี่ยนแปลงพิกัด
            log_action(robot_id, 'Updated coordinates', f"From {previous_coordinates} to ({robot.x}, {robot.y})")

            return {
                'message': 'Robot coordinates updated',
                'robot_id': robot.robot_id,
                'coordinates': {'x': robot.x, 'y': robot.y , 'angle':robot.angle}
            }, 200
        return {'message': 'Robot not found'}, 404