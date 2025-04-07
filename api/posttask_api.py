from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot import Robot
from models.database import db
from flask import request
import requests

class PostTask(Resource):
    def post(self):
        try:
            # รับข้อมูลจาก request
            data = request.get_json()

            # ตรวจสอบว่ามี key ที่จำเป็นใน JSON หรือไม่
            required_keys = ["biz", "process", "lot_no", "product", "from_stocker", "to_stocker"]
            if not all(key in data for key in required_keys):
                return {'message': 'Invalid request: missing required keys'}, 400

            # ดึงค่าที่เกี่ยวข้อง
            from_stk = data.get('from_stocker')
            to_stk = data.get('to_stocker')

            # ค้นหาในฐานข้อมูล
            pickup_dest = Destination.query.filter_by(official_name=from_stk).first()
            to_dest = Destination.query.filter_by(official_name=to_stk).first()

            # ตรวจสอบว่าพบจุดหมายปลายทางหรือไม่
            if not pickup_dest or not to_dest:
                return {'message': 'Invalid from_stocker or to_stocker, destination not found'}, 404

            assign_robot = None
            assign_data = None

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

            # ส่งข้อมูลไปยัง API ของ AssignDestination
            assign_destination_url = "http://localhost:5055/assign/destination"  # เปลี่ยนเป็น URL จริง
            response = requests.post(assign_destination_url, json=assign_data)

            response_data  = response.json()
            info_data["job_no"] = response_data.get("pickup_job_id")

            # ตรวจสอบสถานะการส่งข้อมูล
            if response.status_code == 200 or response.status_code == 202:
                return {"message": "response message", "info": info_data}, 200
            else:
                return {"message": "Failed to assign task", "error": response.json()}, response.status_code

        except Exception as e:
            return {"message": "Internal server error", "error": str(e)}, 500