from flask_restful import Resource, reqparse
from models.destination import Destination
from models.heartbeat import Heartbeat
from models.robot import Robot
from models.robot_log import RobotLog
from models.robot_job import RobotJobQueue
from models.database import db
import json
import math


# สูตร Euclidean Distance สำหรับคำนวณระยะทางในระบบ 2 มิติ
def euclidean_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class AssignDestination(Resource):
    def post(self):
        # กำหนด Parser สำหรับรับข้อมูลจาก Client
        parser = reqparse.RequestParser()
        parser.add_argument('robotid', type=str, required=False, help="Robot id which assigned")
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

        # หาหุ่นยนต์ที่ว่างที่สุด
        # available_robots = Robot.query.filter_by(status='available').all()
        assign_robot = None
        if(args.get('robotid')):
           assign_robot = args.get('robotid')
            
        valid_heartbeats = (
            Heartbeat.query
            .join(Robot)  # เชื่อมโยงกับตาราง Robot
            .filter(Robot.status == 'available', Heartbeat.status =="active")
            .all()
        )

        # if available_robots:
        if valid_heartbeats:
            # หากมีหุ่นยนต์ที่ว่าง ให้มอบหมายงานให้หุ่นยนต์
            closest_robot = None
            closest_distance = float('inf')

            # for robot in available_robots:
            for heartbeat in valid_heartbeats:
                robot = heartbeat.robot
                distance = euclidean_distance(robot.x, robot.y, destination.x, destination.y)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_robot = robot

            if closest_robot:
                

                if pickup:
                    previous_status = closest_robot.status
                    closest_robot.status = 'wait_robot'
                    closest_robot.pickup_id = pickup.id
                    closest_robot.destination_id = destination.id
                    closest_robot.properties = properties

                    pickup_job = RobotJobQueue(
                        job_description=f"Move to pickup location {pickup.name}",
                        destination_name=pickup.name,
                        destination_id=pickup.id,
                        status='processing',
                        assignedto=closest_robot.robot_id,
                        properties=properties
                    )
                    db.session.add(pickup_job)
                    db.session.commit()
                
                    delivery_job = RobotJobQueue(
                        job_description=f"Move to destination {destination.name}",
                        destination_name=destination.name,
                        destination_id=destination.id,
                        status='processing',  # เริ่มทำหลัง pickup เสร็จ
                        assignedto=closest_robot.robot_id,  # ใช้หุ่นยนต์ตัวเดียวกัน
                        properties=properties,
                        parent_job_id=pickup_job.id  # เชื่อมโยงกับ Pickup Job
                    )
                    db.session.add(delivery_job)
                    db.session.commit()

                    log_action(closest_robot.robot_id, 'Assigned destination', f"From {previous_status} to working, Destination: {destination.name}")

                    return {
                        'message': f'Robot {closest_robot.robot_id} is assigned to destination: {destination.name}',
                        'robot_id': closest_robot.robot_id,
                        'pickup_job_id': pickup_job.id,
                        'delivery_job_id': delivery_job.id,
                        'pickup': pickup.name,
                        'destination': destination.name
                    }, 200

                else:
                    # อัพเดทหุ่นยนต์
                    previous_status = closest_robot.status
                    closest_robot.status = 'wait_robot'
                    closest_robot.destination_id = destination.id
                    closest_robot.properties = properties

                    delivery_job = RobotJobQueue(
                        job_description=f"Move to destination {destination.name}",
                        destination_name=destination.name,
                        destination_id=destination.id,
                        status='processing',  # เริ่มทำหลัง pickup เสร็จ
                        assignedto=closest_robot.robot_id,  # ใช้หุ่นยนต์ตัวเดียวกัน
                        properties=properties
                    )
                    db.session.add(delivery_job)
                    db.session.commit()
                
                    log_action(closest_robot.robot_id, 'Assigned destination', f"From {previous_status} to working, Destination: {destination.name}")

                    return {
                        'message': f'Robot {closest_robot.robot_id} is assigned to destination: {destination.name}',
                        'robot_id': closest_robot.robot_id,
                        'destination_job_id':delivery_job.id,
                        'destination': destination.name
                    }, 200

                # บันทึก log การมอบหมาย
        elif(assign_robot):
            
            if pickup:

                    pickup_job = RobotJobQueue(
                        job_description=f"Move to pickup location {pickup.name}",
                        destination_name=pickup.name,
                        destination_id=pickup.id,
                        status='waiting',
                        assignedto=assign_robot,
                        properties=properties
                    )
                    db.session.add(pickup_job)
                    db.session.commit()
                
                    delivery_job = RobotJobQueue(
                        job_description=f"Move to destination {destination.name}",
                        destination_name=destination.name,
                        destination_id=destination.id,
                        status='waiting',  # เริ่มทำหลัง pickup เสร็จ
                        assignedto=assign_robot,  # ใช้หุ่นยนต์ตัวเดียวกัน
                        properties=properties,
                        parent_job_id=pickup_job.id  # เชื่อมโยงกับ Pickup Job
                    )
                    db.session.add(delivery_job)
                    db.session.commit()

                    log_action(assign_robot, 'Assigned destination', f" Destination: {destination.name}")

                    return {
                        'message': f'Robot {assign_robot} is assigned to destination: {destination.name}',
                        'robot_id': assign_robot,
                        'pickup_job_id': pickup_job.id,
                        'delivery_job_id': delivery_job.id,
                        'pickup': pickup.name,
                        'destination': destination.name
                    }, 200

            else:

                    delivery_job = RobotJobQueue(
                        job_description=f"Move to destination {destination.name}",
                        destination_name=destination.name,
                        destination_id=destination.id,
                        status='waiting',  # เริ่มทำหลัง pickup เสร็จ
                        assignedto=assign_robot,  # ใช้หุ่นยนต์ตัวเดียวกัน
                        properties=properties
                    )
                    db.session.add(delivery_job)
                    db.session.commit()
                
                    log_action(assign_robot, 'Assigned destination', f"From {previous_status} to working, Destination: {destination.name}")

                    return {
                        'message': f'Robot {assign_robot} is assigned to destination: {destination.name}',
                        'robot_id': assign_robot,
                        'destination_job_id':delivery_job.id,
                        'destination': destination.name
                    }, 200        
        else:
            # ถ้าไม่มีหุ่นยนต์ว่าง เพิ่มงานลงใน queue
            if pickup:
                pickup_job = RobotJobQueue(
                    job_description=f"Move to pickup location {pickup.name}",
                    destination_name=pickup.name,
                    destination_id=pickup.id,
                    status='waiting',
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
                    f"No available robots, job {pickup_job.id} and {delivery_job.id} added to queue"
                )

                return {
                    'message': 'No available robots, jobs added to queue',
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
                    f"No available robots, job  {delivery_job.id} added to queue"
                )

                return {
                    'message': 'No available robots, jobs added to queue',
                    'delivery_job_id': delivery_job.id,
                    'destination': destination.name
                }, 202