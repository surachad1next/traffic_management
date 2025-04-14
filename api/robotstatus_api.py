from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot_log import RobotLog
from models.robot import Robot
from models.robot_job import RobotJobQueue
from models.database import db
from dotenv import load_dotenv
from flask import request
import json
import os
import uuid
from werkzeug.utils import secure_filename

load_dotenv()
# ROBOT_HOME = "HOME"
# CHARGE_POINT = "CHARGER"
CHARGE_POINT = os.getenv("CHARGE_POINT")
ROBOT_HOME = os.getenv("ROBOT_HOME")
def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class RobotStatus(Resource):
    def get(self, robot_id):
        robot = Robot.query.filter_by(robot_id=robot_id).first()
        if robot:
            # แปลงข้อมูล destination ให้เป็น dictionary
            destination_data = None
            if robot.destination:
                destination_data = {
                    'name': robot.destination.name,
                    'x': robot.destination.x,
                    'y': robot.destination.y
                }

            coordinates = {
                'x': robot.x,
                'y': robot.y
            }
            properties = robot.properties


            log_action(robot_id, 'Checked status', f"Status: {robot.status}, Coordinates: {coordinates}, Destination: {destination_data}")
            
            return {
                'robot_id': robot.robot_id,
                'status': robot.status,
                'battery': robot.battery,
                'group':robot.group,
                'coordinates': coordinates,
                'destination': destination_data
            }, 200
        return {'message': 'Robot not found'}, 404

    def put(self, robot_id):
        # อัพเดทสถานะหุ่นยนต์
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=True, help="Status cannot be blank")
        # parser.add_argument('destination', type=str, help="Destination of the robot")
        args = parser.parse_args()
        robot = Robot.query.filter_by(robot_id=robot_id).first()
        
        if robot:
            previous_status = robot.status
            new_status = args['status']
            print(robot_id)
            print(new_status)

            # หากสถานะคือ "available" ให้เคลียร์ destination และกลับเป็น available
            if (new_status == "available" and robot.status =='wait_robot'):
                job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                job.status = 'waiting'
                job.assignedto = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, job {job.id} to be processing.")
            elif (new_status == "available" and robot.status =='working'):
                job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()
                combined_name = f"{ROBOT_HOME}_{robot.robot_id}"
                destination = Destination.query.filter_by(official_name=combined_name).first()
                robot.destination_id = destination.id  # เคลียร์ destination
                robot.properties = None
                robot.status = 'preempted'
                job.status = 'preempted'
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to preempted, job {job.id} to be preempted.")
            elif (new_status == "available" and robot.status =='preempted'):
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, robot currently home.")
            elif (new_status == "charge" and robot.status =='available'):
                combined_name = f"{CHARGE_POINT}_{robot.robot_id}"
                destination = Destination.query.filter_by(official_name=combined_name).first()
                robot.destination_id = destination.id  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, robot currently home.")
            elif (new_status == "busy" and robot.status =='available'):
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to busy, robot has own job.")
            elif (new_status == "available" and robot.status =='busy'):
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, robot has finish own job.")
            elif (new_status == "maintain" and robot.status =='available'):
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to maintain, robot need to maintain.")
            elif (new_status == "available" and robot.status =='maintain'):
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, robot has finish maintain.")
            elif (new_status == "available" and robot.status =='emergency'):
                if (robot.previous_status =='working'):
                    robot.status = "wait_robot"
                else:
                    robot.status = robot.previous_status
                robot.previous_status = None
                log_action(robot_id, 'Status updated', f"From {previous_status} to available, robot has available now.")
            elif (new_status == "emergency"):
                robot.previous_status = previous_status
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to emergency, robot emergency state.")
            elif (new_status == "pause"):
                robot.previous_status = previous_status
                robot.status = new_status
                log_action(robot_id, 'Status updated', f"From {previous_status} to pause, robot pause state.")
            elif (new_status == "resume"):
                robot.status = previous_status
                robot.previous_status = None
                log_action(robot_id, 'Status updated', f"From {previous_status} to resume, robot resume state.")
            else:
                robot.destination = None  # เคลียร์ destination
                robot.properties = None
                robot.status = new_status

            db.session.commit()

            # บันทึก log การเปลี่ยนแปลงสถานะ
            destination_data = None
            if robot.destination:
                destination_data = {
                    'name': robot.destination.name,
                    'x': robot.destination.x,
                    'y': robot.destination.y
                }

            return {
                'message': 'Robot status updated',
                'robot_id': robot.robot_id,
                'status': robot.status,
                'destination': destination_data
            }, 200

        return {'message': 'Robot not found'}, 404