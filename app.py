#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent.monkey
gevent.monkey.patch_all()
# import gevent_psycopg2
# gevent_psycopg2.monkey_patch()

from flask import Flask ,request
# from flask_restful import Api, Resource, reqparse
from flask_socketio import SocketIO
from datetime import datetime, timedelta
from models import db,Robot,Heartbeat,RobotLog,RobotJobQueue,RobotArea,Destination
from api import api
from socket_io import handle_update_coordinates ,handle_call_robot ,handle_update_status ,handle_get_robot_statuses, handle_heartbeat

import socketio
import click
import multiprocessing

from werkzeug.utils import secure_filename

# from geventwebsocket import WebSocketServer
# from gevent.pywsgi import WSGIServer

import gevent

CHARGE_POINT = "CHARGER"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///robots.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#=======================================================================
############            INIT DB and APP API                  ###########
#=======================================================================

db.init_app(app)

api.init_app(app)
# api = Api(app)
socketio = SocketIO(app,
                    async_mode='gevent',
                    max_http_buffer_size=10000000,
                    cors_allowed_origins="*", 
                    ping_timeout=5, 
                    ping_interval=5, 
                    engineio_logger=False, 
                    logger=False
                    )

#=======================================================================
############        CRATE FLASK APP FOR CLEAR OLD LOGS        ##########
#=======================================================================

@click.command('clear_old_logs')  # ระบุชื่อคำสั่งที่ต้องการใน CLI
def clear_old_logs():
    cutoff_date = datetime.utcnow() - timedelta(days=15)
    old_logs = RobotLog.query.filter(RobotLog.timestamp < cutoff_date).all()

    # บันทึก log ว่ามีการลบ log เก่า
    log_action('system', 'Clear old logs', f"Deleted {len(old_logs)} logs older than {cutoff_date}")
    
    # ลบ log เก่ากว่า 15 วัน
    for log in old_logs:
        db.session.delete(log)
    
    db.session.commit()

    print(f"{len(old_logs)} logs have been deleted.")
    return len(old_logs)

# ฟังก์ชันบันทึก Log
def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()

# เพิ่มคำสั่งให้ Flask CLI
app.cli.add_command(clear_old_logs)

#=======================================================================
############           CRATE Database if not exist            ##########
#=======================================================================

# สร้างฐานข้อมูล (run ครั้งแรก)
with app.app_context():
    db.create_all()


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
            """ ตรวจสอบระดับแบตเตอรี่ของหุ่นยนต์และสั่งให้วิ่งไปยังแท่นชาร์จหากต่ำกว่า 20% """
            robots_need_charge = []

            robots = Robot.query.all()
            for robot in robots:
                try:
                    if robot.battery < 20 and robot.status == "available":
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

        gevent.sleep(5)

def check_heartbeats():
    while True:
        with app.app_context():
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
                    # if heartbeat.robot:
                    #     heartbeat.robot.status = 'inactive'  # อัปเดตสถานะหุ่นยนต์ด้วย
                    inactive_robots.append({
                        'robot_id': heartbeat.robot.robot_id, 
                        'last_seen': str(heartbeat.last_seen)
                    })

            # บันทึกการเปลี่ยนแปลงหากมี
            if inactive_robots:
                db.session.commit()

                socketio.emit('robot_inactive', {'robots': inactive_robots})

        # พักการทำงานเพื่อหลีกเลี่ยงการใช้ CPU สูง
        gevent.sleep(5)  # ตรวจสอบทุก ๆ 5 วินาที

def check_area_robot():
    """ ตรวจสอบว่ามีหุ่นยนต์อยู่ในพื้นที่เดียวกันหรือไม่ แล้วส่ง pause/play ตามลำดับ """
    while True:
        with app.app_context():

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


        gevent.sleep(2)  # พักการทำงานเพื่อหลีกเลี่ยงการใช้ CPU สูง

def check_and_assign_job():
    while True:
        with app.app_context():
            valid_heartbeats = (
                Heartbeat.query
                .join(Robot)
                .filter(Robot.status == 'available', Heartbeat.status == "active")
                .all()
            )

            # ✅ ดึงงานทั้งหมดที่รออยู่ และเรียงให้ pickup มาก่อน delivery
            waiting_jobs = RobotJobQueue.query.filter_by(status='waiting').order_by(RobotJobQueue.parent_job_id.nulls_first()).all()

            for job in waiting_jobs:
                assigned_robot = None

                if job.parent_job_id:  # ✅ เป็น Delivery Job
                    # ✅ หุ่นที่ทำ Pickup Job อยู่คือใคร?
                    parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
                    if not parent_job or parent_job.status != 'processing':
                        continue  

                    assigned_robot = Robot.query.filter_by(pickup_id=parent_job.id, status='wait_robot').first()

                else:  # ✅ เป็น Pickup Job
                    for heartbeat in valid_heartbeats:
                        if heartbeat.robot.status == 'available':
                            assigned_robot = heartbeat.robot
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
                        # print(pickup)
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

        gevent.sleep(1)


# เริ่มงาน background tasks

gevent.spawn(check_and_assign_job)
gevent.spawn(check_heartbeats)
gevent.spawn(check_area_robot)
gevent.spawn(check_battery_levels)
# socketio.start_background_task(target=check_heartbeats)
# socketio.start_background_task(target=check_area_robot)
# socketio.start_background_task(target=check_and_assign_job)

#=======================================================================
############          MAIN FUNCTION OF PYTHON APP             ##########
#=======================================================================
# def start_background_tasks():
#     gevent.spawn(check_and_assign_job)
#     gevent.spawn(check_heartbeats)
#     gevent.spawn(check_area_robot)
#     print("🟢 Background task started!")  # ✅ Debugging

# start_background_tasks()

# if __name__ != "__main__":
#     start_background_tasks()  # ✅ ให้ uwsgi เรียก gevent
def start_ws():
	### IP WINDOWS HOST
    socketio.run(app, host='0.0.0.0', port=5055, debug=False)
    
if __name__ == '__main__':
    # app.run(debug=True)
    # socketio.run(app, host='0.0.0.0', port=5055, debug=False)
    # ใช้ gevent สำหรับ running Flask app
    # http_server = WSGIServer(('0.0.0.0', 5055), app)
    # http_server.serve_forever()
    p_ws = multiprocessing.Process(target=start_ws)

    # 
    # p_flask.start()
    p_ws.start()

    
    # p_flask.join()
    p_ws.join()
