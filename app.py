#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent.monkey
gevent.monkey.patch_all()


from flask import Flask ,request ,current_app
from flask_socketio import SocketIO
from datetime import datetime 
from sqlalchemy import asc, desc, case , select , text
from models import db,Robot,Heartbeat,RobotLog,RobotJobQueue,RobotArea,Destination
from api import api
from socket_io import handle_update_coordinates ,handle_call_robot ,handle_update_status ,handle_get_robot_statuses, handle_heartbeat
from cli.command import clear_old_logs , log_action
from logging_config import setup_logger
from config import Config
from dotenv import load_dotenv
import os
import socketio
# import click
import multiprocessing
import pymysql

pymysql.install_as_MySQLdb()

from werkzeug.utils import secure_filename


import gevent


load_dotenv()

CHARGE_POINT = os.getenv("CHARGE_POINT")

app = Flask(__name__)
app.config.from_object(Config)

#=======================================================================
############            INIT DB and APP API                  ###########
#=======================================================================

db.init_app(app)

api.init_app(app)
# api = Api(app)
socketio = SocketIO(app,
                    async_mode='gevent_uwsgi',
                    # async_mode='gevent',
                    max_http_buffer_size=10000000,
                    cors_allowed_origins='*', 
                    ping_timeout=5, 
                    ping_interval=5, 
                    engineio_logger=False, 
                    logger=True
                    )

#=======================================================================
############                    SYSTEM LOG                    ##########
#=======================================================================

logger = setup_logger()


#=======================================================================
############                   Create View                    ##########
#=======================================================================

def create_view():
    with app.app_context():
        # ตรวจสอบและสร้าง view ถ้ายังไม่มี
        sql = text("""
        CREATE OR REPLACE VIEW view_robot_log AS
        SELECT id, robot_id, action, timestamp, details
        FROM robot_log;
        """)
        db.session.execute(sql)
        db.session.commit()
        

# เพิ่มคำสั่งให้ Flask CLI
app.cli.add_command(clear_old_logs)

#=======================================================================
############           CRATE Database if not exist            ##########
#=======================================================================

# สร้างฐานข้อมูล (run ครั้งแรก)
with app.app_context():
    try:
        create_view()
    except Exception as e:
        print("Error in Create View: %s", e)
        logger.error("Error in Create View: %s", e)
    try:
        db.create_all()
    except Exception as e:
        print("Error in Create database: %s", e)
        logger.error("Error in Create database: %s", e)

#=======================================================================
############            SOCKET IO EVENT FOR ROBOT             ##########
#=======================================================================

socketio.on_event('update_coordinates', handle_update_coordinates)
socketio.on_event('call_robot', handle_call_robot)
socketio.on_event('update_status', handle_update_status)
socketio.on_event('get_robot_statuses', handle_get_robot_statuses)
socketio.on_event('heartbeat', handle_heartbeat)


@socketio.on('connect')
def handle_connect():
    print("SocketIO connection established! : ",request.sid)

@socketio.on('disconnect')
def handle_connect():
    print("SocketIO disconnected !",request.sid)

#=======================================================================
############          GEVENT FOR ROUTING FUNCTION             ##########
#=======================================================================

def check_battery_levels():
    while True:
        with app.app_context():
            try:
            
                """ ตรวจสอบระดับแบตเตอรี่ของหุ่นยนต์และสั่งให้วิ่งไปยังแท่นชาร์จหากต่ำกว่า 20% """
                robots_need_charge = []

                robots = Robot.query.all()
                # print(f"🟢 Checking Battery: {len(robots)} robots")  # ✅ Debugging
                for robot in robots:
                    try:
                        if robot.battery != None:
                            if robot.battery < 20 and robot.status == "available" :
                                robot.status = 'NeedCharge'
                                combined_name = f"{CHARGE_POINT}_{robot.robot_id}"
                                # ค้นหาตำแหน่ง charger ที่อยู่ใน Destination
                                charger =  Destination.query.filter_by(official_name=combined_name).first()
                                if charger:

                                    robot.destination_id = charger.id
                                    robots_need_charge.append({
                                        'robot_id': robot.robot_id,
                                        'battery': robot.battery,
                                        'destination': {'x': charger.x, 'y': charger.y}
                                    })
                    except Exception as e:
                        socketio.emit("error", "Internal server error ", {str(e)})
                        

                # หากมีหุ่นยนต์ที่ต้องชาร์จ แจ้งเตือนและบันทึกลงฐานข้อมูล
                if robots_need_charge:
                    db.session.commit()
                    socketio.emit('robot_need_charge', {'robots': robots_need_charge})

                
            except Exception as e:
                print("Error in battery loop: %s", e)
                logger.error("Error in battery loop: %s", e)
            
            finally:
                db.session.remove()

        gevent.sleep(5)

def check_heartbeats():
    while True:
        with app.app_context():
            try:
                
                timeout_seconds = 20  # ระยะเวลา timeout (วินาที)
                current_time = datetime.utcnow()
                inactive_robots = []

                # ตรวจสอบหุ่นยนต์ที่ heartbeat เกินเวลา
                heartbeats = Heartbeat.query.all()
                print(f"🟢 Checking heartbeats: {len(heartbeats)} robots")  # ✅ Debugging
                for heartbeat in heartbeats:
                    time_diff = (current_time - heartbeat.last_seen).total_seconds()
                    if time_diff > timeout_seconds and heartbeat.status == 'active':
                        heartbeat.status = 'inactive'
                        
                        inactive_robots.append({
                            'robot_id': heartbeat.robot.robot_id, 
                            'last_seen': str(heartbeat.last_seen)
                        })

                # บันทึกการเปลี่ยนแปลงหากมี
                if inactive_robots:
                    db.session.commit()

                    socketio.emit('robot_inactive', {'robots': inactive_robots})

                
            except Exception as e:
                print("Error in heartbeat loop: %s", e)
                logger.error("Error in heartbeat loop: %s", e)
            
            finally:
                db.session.remove()
        
        gevent.sleep(5)  # ตรวจสอบทุก ๆ 5 วินาที      # พักการทำงานเพื่อหลีกเลี่ยงการใช้ CPU สูง
          
def check_area_robot():
    """ ตรวจสอบว่ามีหุ่นยนต์อยู่ในพื้นที่เดียวกันหรือไม่ แล้วส่ง pause/play ตามลำดับ """
    while True:
        with app.app_context():
            try:

                area_robots = (
                    RobotArea.query
                    .join(Robot)
                    .join(Heartbeat, Heartbeat.robot_id == Robot.id) 
                    .filter(Heartbeat.status != 'inactive')
                    .all()
                )

                # เก็บข้อมูลพื้นที่และหุ่นยนต์
                listrobot_area = {}
                robot_areas = {}
                robot_states = {}

                for area_robot in area_robots:
                    area_names = area_robot.get_area_name()
                    robot = area_robot.robot

                    for area in area_names:
                        if area not in listrobot_area:
                            listrobot_area[area] = []

                        listrobot_area[area].append({"robot": robot, "area": area})

                        if robot.robot_id not in robot_areas:
                            robot_areas[robot.robot_id] = set()

                        robot_areas[robot.robot_id].add(area)

                

                # ✅ 1. กำหนด play/pause ตามลำดับการเข้า
                for area, robots in listrobot_area.items():
                    robots = sorted(robots, key=lambda r: r["robot"].areas[0].created_at)

                    for i, r in enumerate(robots):
                        robot_id = r["robot"].robot_id
                        # ใช้ .get() เพื่อรักษาค่า play/pause เดิม ถ้าเคยกำหนดไปแล้ว
                        if robot_id not in robot_states:
                            robot_states[robot_id] = "play" if i == 0 else "pause"

                # ✅ 2. ตรวจสอบว่าหุ่นยนต์อยู่หลายพื้นที่ และ force pause ถ้าจำเป็น
                for robot_id, areas in robot_areas.items():
                    if len(areas) > 1:  # หุ่นยนต์ที่อยู่ในหลายพื้นที่เท่านั้นที่ต้องถูกตรวจสอบ
                        should_pause = any(
                            other["robot"].robot_id != robot_id and 
                            robot_states.get(other["robot"].robot_id, "play") == "pause"
                            for a in areas
                            for other in listrobot_area[a]
                        )


                        first_area = min(areas)  # เอาพื้นที่แรกที่พบ
                        first_robot = listrobot_area[first_area][0]["robot"].robot_id  # หุ่นยนต์แรกสุดของพื้นที่นี้

                        if should_pause and robot_id != first_robot:
                            robot_states[robot_id] = "pause"



                # ✅ 3. อัปเดตค่า state ใน listrobot_area
                for area, robots in listrobot_area.items():
                    for r in robots:
                        r["state"] = robot_states[r["robot"].robot_id]



                if listrobot_area:
                    robot_control_data = [
                        {"robot_id": r["robot"].robot_id, "state": r["state"], "area": r["area"]}
                        for area in listrobot_area.values()
                        for r in area
                    ]
                    socketio.emit("robot_control", robot_control_data)

                
            except Exception as e:
                print("Error in area robot loop: %s", e)
                logger.error("Error in area robot loop: %s", e)
            
            finally:
                db.session.remove()

        gevent.sleep(2)  # พักการทำงานเพื่อหลีกเลี่ยงการใช้ CPU สูง

def check_and_assign_job():
    while True:
        with app.app_context():
            try:
                active_robot_ids_subquery = (
                    select(Heartbeat.robot_id)
                    .join(Robot)
                    .filter(
                        Robot.status == 'available',
                        Heartbeat.status == 'active'
                    )
                    .scalar_subquery()
                )

                valid_heartbeats = (
                    Heartbeat.query
                    .filter(Heartbeat.robot_id.in_(active_robot_ids_subquery))
                    .all()
                )

                order_expr = case(
                    (RobotJobQueue.parent_job_id == None, 0),
                    else_=1
                )
                
                waiting_jobs = (
                    RobotJobQueue.query
                    .filter_by(status='waiting')
                    .order_by(order_expr, RobotJobQueue.parent_job_id)
                    .all()
                )
                for job in waiting_jobs:
                    assigned_robot = None

                    if job.parent_job_id:  # ✅ เป็น Delivery Job
                        # ✅ หุ่นที่ทำ Pickup Job อยู่คือใคร?
                        parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
                        if not parent_job or parent_job.status != 'processing':
                            continue  

                        assigned_robot = Robot.query.filter_by(pickup_id=parent_job.id, status='wait_robot').first()

                    else:
                        print(f"🟢 Checking and assgin Job: {len(valid_heartbeats)} robots")  # ✅ Debugging
                        for heartbeat in valid_heartbeats:
                            robot = heartbeat.robot

                            if robot.status != 'available':
                                continue

                            if job.group:
                                if not robot.group or robot.group != job.group:
                                    continue  # ข้ามหุ่นที่ไม่มี group หรือ group ไม่ตรง

                            assigned_robot = robot
                            break

                    if assigned_robot:
                        # ✅ อัปเดตสถานะหุ่นยนต์และงาน
                        assigned_robot.status = 'wait_robot'
                        assigned_robot.pickup_id = job.destination_id
                        assigned_robot.properties = job.properties
                        job.status = 'processing'
                        job.assignedto = assigned_robot.robot_id
                        # print("assign: ",job)
                        if job.parent_job_id is None:  # ✅ ถ้าเป็น Pickup Job → เก็บ pickup_id
                            pickup = RobotJobQueue.query.filter_by(parent_job_id=job.id).first()
                            if pickup:
                                assigned_robot.destination_id = pickup.destination_id

                        db.session.commit()

                        log_action(
                            assigned_robot.robot_id,
                            'Assigned job',
                            f"Assigned job {job.id} Destination: {job.destination_name} to robot {assigned_robot.robot_id}"
                        )

                        # ✅ ถ้าเป็น Pickup Job → Assign Delivery Job ทันที
                        if job.parent_job_id is None:
                            child_job = RobotJobQueue.query.filter_by(parent_job_id=job.id, status='waiting').first()
                            if child_job:
                                child_job.status = 'processing'
                                child_job.assignedto = assigned_robot.robot_id
                                db.session.commit()

                                log_action(
                                    assigned_robot.robot_id,
                                    'Assigned job',
                                    f"Assigned delivery job {child_job.id} Destination: {child_job.destination_name} to robot {assigned_robot.robot_id}"
                                )
                
            except Exception as e:
                print("Error in job assign loop: %s", e)
                logger.error("Error in job assign loop: %s", e)
            
            finally:
                db.session.remove()
        
        gevent.sleep(1)
        


# เริ่มงาน background tasks

gevent.spawn(check_and_assign_job)
gevent.spawn(check_heartbeats)
gevent.spawn(check_area_robot)
gevent.spawn(check_battery_levels)
 
def start_ws():
	### IP WINDOWS HOST
    socketio.run(app, host='0.0.0.0', port=5055, debug=False)
    
if __name__ == '__main__':
 
    p_ws = multiprocessing.Process(target=start_ws)

 
    p_ws.start()

 
    p_ws.join()
