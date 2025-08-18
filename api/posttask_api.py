from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot import Robot
from models.robot_log import RobotLog
from models.database import db
from flask import request
import requests
from dotenv import load_dotenv
import os
load_dotenv()
from logging_config import setup_logger
logger = setup_logger()

SERVICE_PORT = os.getenv("SERVICE_PORT", 5055)

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class PostTask(Resource):
    def post(self):
        try:
            # รับข้อมูลจาก request
            data = request.get_json()

            # ตรวจสอบว่ามี key ที่จำเป็นใน JSON หรือไม่
            required_keys = ["biz", "process", "lot_no", "product", "from_stocker", "to_stocker"]
            if not all(key in data for key in required_keys):
                logger.info(f'POSTTASK : Invalid request: missing required keys')
                log_action(f'POSTTASK : Invalid request: missing required keys')
                return {'message': 'Invalid request: missing required keys'}, 400

            # ดึงค่าที่เกี่ยวข้อง
            from_stk = data.get('from_stocker')
            to_stk = data.get('to_stocker')

            # ค้นหาในฐานข้อมูล
            pickup_dest = Destination.query.filter_by(official_name=from_stk).first()
            to_dest = Destination.query.filter_by(official_name=to_stk).first()

            # ตรวจสอบว่าพบจุดหมายปลายทางหรือไม่
            if not pickup_dest or not to_dest:
                logger.info(f'POSTTASK : Invalid from_stocker or to_stocker, destination not found')
                log_action(f'POSTTASK : Invalid from_stocker or to_stocker, destination not found')
                return {'message': 'Invalid from_stocker or to_stocker, destination not found'}, 404

            assign_robot = None
            assign_data = None
            group_robot = None
            

            info_data = {
                    "lot_no":data.get('lot_no'),
                    "status": "W",
                    "from_stocker":from_stk,
                    "from_level":data.get('from_level'),
                    "from_block":data.get('from_block'),
                    "to_stocker":to_stk,
                    "to_level":data.get('to_level'),
                    "to_block":data.get('to_block'),
                }

            if(data.get('RobotName')):
                robotname = data.get('RobotName')
                assign_robot  = Robot.query.filter_by(robot_id=robotname).first()
                if(assign_robot == None):    
                    logger.info(f'Robot Name not found: {robotname}')
                    return {'message': f'Robot Name not found: {robotname}'}, 400
                
                assign_data = {
                    "robotid":assign_robot.robot_id,
                    "pickup_name": pickup_dest.name,
                    "destination_name": to_dest.name,
                    "properties": {
                        "ui": data  # ใส่ข้อมูลทั้งหมดของ task ไว้ใน properties.ui
                    }
                }
                info_data["assigned_to"] = assign_robot.robot_id
            else:
                assign_data = {
                    "pickup_name": pickup_dest.name,
                    "destination_name": to_dest.name,
                    "properties": {
                        "ui": data  # ใส่ข้อมูลทั้งหมดของ task ไว้ใน properties.ui
                    }
                }

            if(data.get('group')):
                group_robot = data.get('group')

                assign_data["group"] = group_robot
                
            # ส่งข้อมูลไปยัง API ของ AssignDestination
            assign_destination_url = "http://localhost:"+SERVICE_PORT+"/assign/destination"  # เปลี่ยนเป็น URL จริง
            response = requests.post(assign_destination_url, json=assign_data)

            response_data  = response.json()
            info_data["job_no"] = response_data.get("pickup_job_id")

            # ตรวจสอบสถานะการส่งข้อมูล
            if response.status_code == 200 or response.status_code == 202:
                return {"message": "response message", "info": info_data}, 200
            else:
                logger.info(f'Failed to assign task: error: {response.json()}')
                log_action(f'Failed to assign task: error: {response.json()}')
                return {"message": "Failed to assign task", "error": response.json()}, response.status_code

        except Exception as e:
            logger.info(f'Internal server error: error: {str(e)}')
            log_action(f'Internal server error: error: {str(e)}')
            return {"message": "Internal server error", "error": str(e)}, 500