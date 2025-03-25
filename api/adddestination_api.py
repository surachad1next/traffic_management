from flask_restful import Resource, reqparse
from models.destination import Destination
from models.robot_log import RobotLog
from models.database import db
from flask import request
import json
import os
import uuid
from werkzeug.utils import secure_filename


def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

class AddDestination(Resource):
    def get(self):
        existing_destinations = Destination.query.all()
        destination_list = [{
            'id': existing_destination.id,
            'name': existing_destination.name,
            'official_name':existing_destination.official_name,
            'unique_code':existing_destination.unique_code,
            'x': existing_destination.x,
            'y': existing_destination.y
        } for existing_destination in existing_destinations]
        return {
            'message': 'Get Destination Successful',
            'destinations': destination_list
        }, 201

    def post(self):
        # กำหนด Parser สำหรับรับข้อมูลจาก Client
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        
        file = request.files['file']
        
        # ตรวจสอบว่าไฟล์มีชื่อหรือไม่
        if file.filename == '':
            return {'message': 'No selected file'}, 400

        # ตรวจสอบว่าไฟล์เป็น JSON หรือไม่
        if not file.filename.endswith('.smap'):
            return {'message': 'Invalid file type. Please upload a JSON file.'}, 400

        # กำหนดที่เก็บไฟล์ในเซิร์ฟเวอร์
        upload_folder = 'uploads/'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # สร้างชื่อไฟล์ที่ปลอดภัย
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)

        # บันทึกไฟล์ลงในเซิร์ฟเวอร์
        file.save(file_path)

        # อ่านข้อมูลจากไฟล์ JSON ที่ส่งเข้ามา
        try:
            destinations = self.extract_destination_from_json(file_path)
        except Exception as e:
            return {'message': f"Error processing the file: {str(e)}"}, 400

        # ตรวจสอบและเพิ่มข้อมูลแต่ละจุดหมายปลายทางลงในฐานข้อมูล
        for destination in destinations:
            instance_name = destination['instanceName']
            pos = destination['pos']
            x, y = pos.get('x',0), pos.get('y',0)

            # ตรวจสอบว่ามีจุดหมายปลายทางนี้ในระบบแล้วหรือไม่
            existing_destination = Destination.query.filter_by(name=instance_name).first()
            if existing_destination:
                continue  # ถ้ามีแล้วก็ข้ามไป
            
            # สร้างข้อมูลจุดหมายปลายทางใหม่
            new_destination = Destination(
                name=instance_name,
                x=x,
                y=y
            )

            # เพิ่มข้อมูลลงในฐานข้อมูล
            db.session.add(new_destination)
            db.session.commit()

            # บันทึก Log
            log_action("system", "Add destination", f"Added destination: {instance_name}")

        return {
            'message': 'Destinations added successfully',
            'destinations': destinations
        }, 201

    def extract_destination_from_json(self, file_path):
        try:
            # อ่านข้อมูลจากไฟล์ JSON
            with open(file_path, 'r') as file:
                data = json.load(file)

            # ดึงข้อมูลจาก advancedPointList
            advanced_point_list = data.get('advancedPointList', [])

            destinations = []

            # วนลูปผ่าน advancedPointList และดึง instanceName และ pos
            for point in advanced_point_list:
                instance_name = point.get('instanceName')
                pos = point.get('pos', {})
                if instance_name and pos:
                    destination = {
                        'instanceName': instance_name,
                        'pos': pos
                    }
                    destinations.append(destination)

            return destinations

        except json.JSONDecodeError:
            raise ValueError("Failed to decode the JSON in the file.")
        except Exception as e:
            raise ValueError(f"An error occurred while processing the file: {str(e)}")
        
    def put(self):
        # กำหนด Parser สำหรับรับข้อมูลจาก Client
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Destination name cannot be blank")
        parser.add_argument('x', type=float, required=True, help="Destination X coordinate cannot be blank")
        parser.add_argument('y', type=float, required=True, help="Destination Y coordinate cannot be blank")
        parser.add_argument('official_name', type=str, required=False, help="Official name of this coordinate")
        parser.add_argument('unique_code', type=str, required=False, help="Unique name of this coordinate")
        args = parser.parse_args()

        # ตรวจสอบว่ามีจุดหมายปลายทางนี้ในระบบแล้วหรือไม่
        existing_destination = Destination.query.filter_by(name=args['name']).first()
        if existing_destination:
            return {'message': 'Destination already exists'}, 400

        # ✅ สร้าง Unique Code อัตโนมัติถ้ายังไม่มี
        unique_code = args.get('unique_code') or str(uuid.uuid4())[:8]

        # ✅ สร้างข้อมูลจุดหมายปลายทางใหม่
        new_destination = Destination(
            name=args['name'],
            x=args['x'],
            y=args['y'],
            official_name=args.get('official_name'),  # รับค่า หรือเป็น None
            unique_code=unique_code  # ใช้ค่าที่กำหนด หรือสร้างใหม่
        )

        # ✅ เพิ่มข้อมูลลงในฐานข้อมูล
        try:
            db.session.add(new_destination)
            db.session.commit()

            # บันทึก Log
            log_action("system", "Add destination", f"Added destination: {new_destination.name} (Code: {new_destination.unique_code})")

            return {
                'message': 'Destination added successfully',
                'destination': {
                    'name': new_destination.name,
                    'official_name': new_destination.official_name,
                    'unique_code': new_destination.unique_code,
                    'x': new_destination.x,
                    'y': new_destination.y
                }
            }, 201

        except Exception as e:
            db.session.rollback()
            log_action("system", "Add destination failed", f"Error: {str(e)}")

            return {'message': 'Destination addition failed', 'error': str(e)}, 500
    
    def delete(self):
        # รับพารามิเตอร์ชื่อจุดหมายปลายทางจากคำขอ
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help="Destination name cannot be blank")
        parser.add_argument('all', type=bool, required=False, help="Delete all Destination")
        args = parser.parse_args()
        if bool(args['all']): 
            db.session.query(Destination).delete()
            db.session.commit()
            log_action("system", "Delete destination", f"Deleted destination: ALL")

            return {'message': "All destinations deleted successfully"}, 200
        elif args.get('name'):
            # ตรวจสอบว่าจุดหมายปลายทางมีอยู่ในระบบหรือไม่
            destination = Destination.query.filter_by(name=args['name']).first()
            if not destination:
                return {'message': f"Destination '{args['name']}' not found"}, 404

            # ลบข้อมูลจุดหมายปลายทาง
            db.session.delete(destination)
            db.session.commit()

            # บันทึก Log การลบ
            log_action("system", "Delete destination", f"Deleted destination: {args['name']}")

            return {'message': f"Destination '{args['name']}' deleted successfully"}, 200

        return {'message': "Invalid request: Provide either 'name' or 'all' parameter"}, 400