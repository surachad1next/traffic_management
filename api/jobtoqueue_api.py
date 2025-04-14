from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot_job import RobotJobQueue
from models.robot_log import RobotLog
from models.database import db
import json

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class JobToQueue(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('pickup_name', type=str, required=False, help="Pickup location cannot be blank")
        parser.add_argument('destination_name', type=str, required=True, help="Destination name cannot be blank")
        parser.add_argument('properties', type=str, help="Robot Properties")
        args = parser.parse_args()

        # หาจุดหมายปลายทางจากชื่อ
        pickup = None  # ตั้งค่าเริ่มต้นเป็น None
        if args.get('pickup_name'):
            try:
                pickup = Destination.query.filter_by(name=args['pickup_name']).first()
            except Exception as e:
                return {'message': f'Pickup location not found: {str(e)}'}, 500

        try:
            destination = Destination.query.filter_by(name=args['destination_name']).first()
        except Exception as e:
            return {'message': f'Error querying destination: {str(e)}'}, 500
        import ast
        properties_dict = ast.literal_eval(args['properties'])
        properties = json.dumps(properties_dict)
        # print(properties)
        if not destination:
            return {'message': 'Destination not found'}, 400

        # เพิ่มงานลงใน queue
        if pickup:
                pickup_job = RobotJobQueue(
                    job_description=f"Move to pickup location {pickup.name}",
                    destination_name=pickup.name,
                    destination_id=pickup.id,
                    properties=properties
                )
                db.session.add(pickup_job)
                db.session.commit()

                delivery_job = RobotJobQueue(
                    job_description=f"Move to destination {destination.name}",
                    destination_name=destination.name,
                    destination_id=destination.id,
                    status='waiting',
                    properties=properties,
                    parent_job_id=pickup_job.id  # เชื่อมโยงกับ Pickup Job
                )
                db.session.add(delivery_job)
                db.session.commit()

                log_action(
                    'system',
                    'Assigned job to queue',
                    f"Job {pickup_job.id} and {delivery_job.id} added to queue"
                )

                return {
                    'message': 'Jobs added to queue',
                    'pickup_job_id': pickup_job.id,
                    'delivery_job_id': delivery_job.id,
                    'pickup': pickup.name,
                    'destination': destination.name
                }, 202

        else:
                delivery_job = RobotJobQueue(
                    job_description=f"Move to destination {destination.name}",
                    destination_name=destination.name,
                    destination_id=destination.id,
                    status='waiting',
                    properties=properties
                )
                db.session.add(delivery_job)
                db.session.commit()

                log_action(
                    'system',
                    'Assigned job to queue',
                    f"Job  {delivery_job.id} added to queue"
                )

                return {
                    'message': 'Jobs added to queue',
                    'delivery_job_id': delivery_job.id,
                    'destination': destination.name
                }, 201

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int, required=True, help="Job ID cannot be blank")
        args = parser.parse_args()

        job = RobotJobQueue.query.filter_by(id=args['job_id']).first()
        if not job:
            return {'message': f"Job with ID {args['job_id']} not found"}, 404

        if job.status != 'waiting':
            return {
                'message': f"Job can only be deleted if status is 'waiting'. Current status: {job.status}"
            }, 400

        deleted_jobs = []

        try:
            # ✅ ลบ child jobs ของ job นี้ก่อนเสมอ
            child_jobs = RobotJobQueue.query.filter_by(parent_job_id=job.id).all()
            for child in child_jobs:
                if child.status == 'waiting':
                    db.session.delete(child)
                    deleted_jobs.append(child.id)

            # ✅ ลบ job นี้ (ไม่ว่าจะเป็น parent หรือ child)
            db.session.delete(job)
            db.session.commit()
            
            deleted_jobs.append(job.id)

            # ✅ ถ้า job นี้เป็น child → ลบ parent ด้วยถ้า status ยัง waiting และยังไม่ถูกลบ
            if job.parent_job_id:
                parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
                if parent_job and parent_job.status == 'waiting' and parent_job.id not in deleted_jobs:
                    db.session.delete(parent_job)
                    deleted_jobs.append(parent_job.id)

            db.session.commit()

            log_action("system", "Delete job", f"Deleted job(s) with ID(s): {deleted_jobs}")
            return {'message': f"Deleted job(s) with ID(s): {deleted_jobs}"}, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f"Error deleting job: {str(e)}"}, 500
