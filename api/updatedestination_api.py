from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot_log import RobotLog
from models.database import db

def log_action(action, details=None):
    """ ฟังก์ชันบันทึก Log การเปลี่ยนแปลง """
    log_entry = RobotLog(robot_id="SYSTEM", action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class UpdateDestination(Resource):
    def put(self, destination_id):
        """ API สำหรับแก้ไขข้อมูล Destination โดยแก้เฉพาะฟิลด์ที่ส่งเข้ามา และบันทึก Log """

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=False, help="New name for the destination")
        parser.add_argument('official_name', type=str, required=False, help="New official name")
        parser.add_argument('unique_code', type=str, required=False, help="New unique code")
        parser.add_argument('x', type=float, required=False, help="New X coordinate")
        parser.add_argument('y', type=float, required=False, help="New Y coordinate")
        args = parser.parse_args()

        # ค้นหา Destination ตาม ID
        destination = db.session.get(Destination, destination_id)
        if not destination:
            return {'message': 'Destination not found'}, 404

        updated_fields = []
        log_details = []

        # อัปเดตค่าตามที่ได้รับมา และบันทึก Log
        if args['name']:
            existing_destination = Destination.query.filter_by(name=args['name']).first()
            if existing_destination and existing_destination.id != destination_id:
                return {'message': 'Name already exists'}, 400
            log_details.append(f"name: {destination.name} → {args['name']}")
            destination.name = args['name']
            updated_fields.append('name')

        if args['official_name']:
            log_details.append(f"official_name: {destination.official_name} → {args['official_name']}")
            destination.official_name = args['official_name']
            updated_fields.append('official_name')

        if args['unique_code']:
            existing_destination = Destination.query.filter_by(unique_code=args['unique_code']).first()
            if existing_destination and existing_destination.id != destination_id:
                return {'message': 'Unique code already exists'}, 400
            log_details.append(f"unique_code: {destination.unique_code} → {args['unique_code']}")
            destination.unique_code = args['unique_code']
            updated_fields.append('unique_code')

        if args['x']:
            log_details.append(f"x: {destination.x} → {args['x']}")
            destination.x = args['x']
            updated_fields.append('x')

        if args['y']:
            log_details.append(f"y: {destination.y} → {args['y']}")
            destination.y = args['y']
            updated_fields.append('y')

        if updated_fields:
            db.session.commit()

            # บันทึก Log
            log_action(f"Updated Destination {destination_id}", ", ".join(log_details))

            return {
                'message': 'Destination updated successfully',
                'updated_fields': updated_fields,
                'destination': {
                    'id': destination.id,
                    'name': destination.name,
                    'official_name': destination.official_name,
                    'unique_code': destination.unique_code,
                    'x': destination.x,
                    'y': destination.y
                }
            }, 200
        else:
            return {'message': 'No fields updated'}, 400
