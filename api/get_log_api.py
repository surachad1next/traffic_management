from flask_restful import Resource, reqparse
from models.robot_view_log import ViewRobotLog
from models.robot_log import RobotLog
from models.database import db
from sqlalchemy import or_, and_
from datetime import datetime

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class GetLog(Resource):

    def post(self):
        # การเพิ่มหุ่นยนต์ใหม่ พร้อมพิกัด x และ y
        parser = reqparse.RequestParser()
        parser.add_argument('robot_id', type=str, required=False, help="Robot ID")
        parser.add_argument('date_from', type=str, required=False, help="From date (ISO format)")
        parser.add_argument('date_to', type=str, required=False, help="To date (ISO format)")
        parser.add_argument('incomplete_only', type=bool, required=False, default=False, help="Search for incomplete logs only")
        args = parser.parse_args()

        query = ViewRobotLog.query

        # ค้นหาตาม robot_id
        if args['robot_id']:
            query = query.filter(ViewRobotLog.robot_id == args['robot_id'])

        # ค้นหาตามช่วงเวลา
        if args['date_from']:
            try:
                date_from = datetime.fromisoformat(args['date_from'])
                query = query.filter(ViewRobotLog.timestamp >= date_from)
            except ValueError:
                return {'error': 'Invalid date_from format. Use ISO format.'}, 400

        if args['date_to']:
            try:
                date_to = datetime.fromisoformat(args['date_to'])
                query = query.filter(ViewRobotLog.timestamp <= date_to)
            except ValueError:
                return {'error': 'Invalid date_to format. Use ISO format.'}, 400

        # ค้นหาเฉพาะ logs ที่มีคำว่า incomplete
        if args['incomplete_only']:
            query = query.filter(
                or_(
                    ViewRobotLog.action.ilike('%incomplete%'),
                    ViewRobotLog.details.ilike('%incomplete%')
                )
            )

        logs = query.order_by(ViewRobotLog.timestamp.desc()).all()

        if logs:
            return {
                'message': f"Found {len(logs)} log(s)",
                'info': [log.serialize() for log in logs]
            }, 200
        else:
            return {'message': 'No logs found matching the criteria'}, 404
        