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
            required_keys = ["Biz", "Process", "LotNo", "ProductType", "FromSTK", "ToSTK"]
            if not all(key in data for key in required_keys):
                return {'message': 'Invalid request: missing required keys'}, 400

            # ดึงค่าที่เกี่ยวข้อง
            from_stk = data.get('FromSTK')
            to_stk = data.get('ToSTK')

            # ค้นหาในฐานข้อมูล
            pickup_dest = Destination.query.filter_by(unique_code=from_stk).first()
            to_dest = Destination.query.filter_by(unique_code=to_stk).first()

            # ตรวจสอบว่าพบจุดหมายปลายทางหรือไม่
            if not pickup_dest or not to_dest:
                return {'message': 'Invalid FromSTK or ToSTK, destination not found'}, 404

            assign_robot = None
            assign_data = None

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

            # ตรวจสอบสถานะการส่งข้อมูล
            if response.status_code == 200 or response.status_code == 202:
                return {"message": "Task assigned successfully", "data": assign_data}, response.status_code
            else:
                return {"message": "Failed to assign task", "error": response.json()}, response.status_code

        except Exception as e:
            return {"message": "Internal server error", "error": str(e)}, 500