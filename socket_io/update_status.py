from flask_socketio import SocketIO, emit
from models.robot import Robot
from models.database import db
from models.robot_log import RobotLog
from models.robot_job import RobotJobQueue
import requests
import json
from dotenv import load_dotenv
import os
load_dotenv()

POST_STATE = os.getenv("POST_STATE")
POST_STATE_ON = bool(os.getenv("POST_STATE_ON",False))

def log_action(robot_id, action, details=None):
    # ใช้ UTC เวลาตั้งต้น แล้วแปลงใน Log
    log_entry = RobotLog(robot_id=robot_id, action=action, details=details)
    db.session.add(log_entry)
    db.session.commit()


def handle_update_status(data):
    # robot_id = data['robot_id']
    # rstatus = data['status']  # ค่าที่หุ่นยนต์ส่งกลับ เช่น 'acknowledged', 'done'
    robot_id = data.get('robot_id')
    status = data.get('status')

    # print(robot_id)
    # print(status)

    # ค้นหาหุ่นยนต์
    robot = Robot.query.filter_by(robot_id=robot_id).first()
    if not robot:
        emit('error', {'message': 'Robot not found'})
        return

    previous_status = robot.status

    # ถ้าหุ่นยนต์ตอบรับคำสั่ง
    if (robot.status == 'wait_robot') and status == 'acknowledged':
        robot.status = 'working'  # เปลี่ยนสถานะจาก wait_robot เป็น working
        log_action(robot_id,f"From wait_robot to {robot.status}", 'Robot acknowledged and started working.')
        db.session.commit()

        # ส่งการตอบรับกลับไปหาหุ่นยนต์
        emit('status_updated', {
            'message': f'Robot {robot_id} has acknowledged and is now working',
            'code': 200
        })

    elif robot.status == 'working' and status == 'pickupdone':
        job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()

        if not job:
            emit('error', {'message': f'No processing job found for robot {robot_id}'})
            return
        
        log_action(robot_id,f"From working to {status}", f'Robot has pickup completed , currently robot is now delivery.')
        try:
            properties = json.loads(job.properties)
            assign_data = {
                "message": "Success Transfer",
                "info": {
                        "lot_no": properties["ui"]["lot_no"],
                        "status": "R",
                        "from_stocker": properties["ui"]["from_stocker"],
                        "from_level": properties["ui"]["from_level"],
                        "from_block": properties["ui"]["from_block"],
                        "to_stocker": properties["ui"]["to_stocker"],
                        "to_level": properties["ui"]["to_level"],
                        "to_block": properties["ui"]["to_block"],
                        "assigned_to": job.assignedto,
                        "job_no": job.id
                    }
                }

            assign_destination_url = POST_STATE  # เปลี่ยนเป็น URL จริง
            if(POST_STATE_ON):
                response = requests.post(assign_destination_url, json=assign_data)
        except Exception as e:
            pass

        emit('status_updated', {
            'message': f'Robot {robot_id} has pickup completed , currently robot is now delivery',
            'code': 200
        })

    elif robot.status == 'working' and status == 'done':
        job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()

        if not job:
            emit('error', {'message': f'No processing job found for robot {robot_id}'})
            return

        robot.status = 'available'  # เปลี่ยนสถานะจาก working เป็น available
        robot.pickup_id = None
        robot.destination = None
        robot.properties = None
        job.status = 'completed'
        job.destination_id = None
        # job.properties = None
        log_action(robot_id,f"From working to {robot.status}", f'Robot has completed {job.destination_name} at the task {job.id}, currently robot is now available.')
        try:
            properties = json.loads(job.properties)
            assign_data = {
                "message": "Success Transfer",
                "info": {
                        "lot_no": properties["ui"]["lot_no"],
                        "status": "C",
                        "from_stocker": properties["ui"]["from_stocker"],
                        "from_level": properties["ui"]["from_level"],
                        "from_block": properties["ui"]["from_block"],
                        "to_stocker": properties["ui"]["to_stocker"],
                        "to_level": properties["ui"]["to_level"],
                        "to_block": properties["ui"]["to_block"],
                        "assigned_to": job.assignedto,
                        "job_no": job.id
                    }
                }

            assign_destination_url = POST_STATE  # เปลี่ยนเป็น URL จริง
            if(POST_STATE_ON):
                response = requests.post(assign_destination_url, json=assign_data)
        except Exception as e:
            pass    

        # ✅ ถ้ามี Parent Job → เปลี่ยนสถานะเป็น completed ด้วย
        if job.parent_job_id:
            parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
            if parent_job and parent_job.status != 'completed':
                parent_job.status = 'completed'
                parent_job.destination_id = None
                parent_job.parent_job_id = None
                log_action(robot_id, "Parent job completed", f"Parent job {parent_job.id} is now completed.")

        # ✅ ถ้ามี Child Job → เปลี่ยนสถานะเป็น completed ด้วย
        child_jobs = RobotJobQueue.query.filter_by(parent_job_id=job.id, status='processing').all()
        for child in child_jobs:
            child.status = 'completed'
            child.destination_id = None
            child.parent_job_id = None
            log_action(robot_id, "Child job completed", f"Child job {child.id} is now completed.")

        
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has completed {job.destination_name} at the task {job.id}, currently robot is now available',
            'code': 202
        })
        
    elif robot.status == 'charging' and status == 'done':
        job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()

        if not job:
            emit('error', {'message': f'No processing job found for robot {robot_id}'})
            return

        robot.status = 'charging'  # เปลี่ยนสถานะจาก working เป็น available
        robot.pickup_id = None
        robot.destination = None
        robot.properties = None
        job.status = 'completed'
        job.destination_id = None
        # job.properties = None
        log_action(robot_id,f"From charging to {robot.status}", f'Robot has completed {job.destination_name} at the task {job.id}, currently robot is now available.')
        try:
            properties = json.loads(job.properties)
            assign_data = {
                "message": "Success Transfer",
                "info": {
                        "lot_no": properties["ui"]["lot_no"],
                        "status": "C",
                        "from_stocker": properties["ui"]["from_stocker"],
                        "from_level": properties["ui"]["from_level"],
                        "from_block": properties["ui"]["from_block"],
                        "to_stocker": properties["ui"]["to_stocker"],
                        "to_level": properties["ui"]["to_level"],
                        "to_block": properties["ui"]["to_block"],
                        "assigned_to": job.assignedto,
                        "job_no": job.id
                    }
                }

            assign_destination_url = POST_STATE  # เปลี่ยนเป็น URL จริง
            if(POST_STATE_ON):
                response = requests.post(assign_destination_url, json=assign_data)
        except Exception as e:
            pass    

        # ✅ ถ้ามี Parent Job → เปลี่ยนสถานะเป็น completed ด้วย
        if job.parent_job_id:
            parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
            if parent_job and parent_job.status != 'completed':
                parent_job.status = 'completed'
                parent_job.destination_id = None
                parent_job.parent_job_id = None
                log_action(robot_id, "Parent job completed", f"Parent job {parent_job.id} is now completed.")

        # ✅ ถ้ามี Child Job → เปลี่ยนสถานะเป็น completed ด้วย
        child_jobs = RobotJobQueue.query.filter_by(parent_job_id=job.id, status='processing').all()
        for child in child_jobs:
            child.status = 'completed'
            child.destination_id = None
            child.parent_job_id = None
            log_action(robot_id, "Child job completed", f"Child job {child.id} is now completed.")

        
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has completed {job.destination_name} at the task {job.id}, currently robot is now available',
            'code': 202
        })
        
    elif(robot.status == 'NeedCharge') and status == 'acknowledged':
        robot.status = 'gotocharger'  # เปลี่ยนสถานะจาก NeedCharge เป็น gotocharger
        log_action(robot_id,f"From NeedCharge to {robot.status}", 'Robot acknowledged and started goto charger.')
        db.session.commit()

        # ส่งการตอบรับกลับไปหาหุ่นยนต์
        emit('status_updated', {
            'message': f'Robot {robot_id} has acknowledged and is goto charger',
            'code': 200
        })
    elif robot.status == 'working' and status == 'cancleall':
        canclealljob(robot_id,state="working")
    
    elif robot.status == 'pause' and status == 'cancleall':
        canclealljob(robot_id,state="working")

    elif robot.status == 'emergency' and status == 'cancleall':
        canclealljob(robot_id,state="working")

    elif robot.status == 'busy' and status == 'cancleall':
        canclealljob(robot_id)

    elif robot.status == 'preempted' and status == 'done':
        robot.status = 'available'  # เปลี่ยนสถานะจาก working เป็น available
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From preempted to {robot.status}", f'Robot has completed go home, currently robot is now available.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has completed go home, currently robot is now available.',
            'code': 202
        })
    elif robot.status == 'available' and status == 'busy':
        robot.status = 'busy'  
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From avaliable to {robot.status}", f'Robot has own job, currently robot is now busy.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has own job, currently robot is now busy.',
            'code': 203
        })
    elif robot.status == 'busy' and status == 'available':
        robot.status = 'available'  
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From busy to {robot.status}", f'Robot has finish own job, currently robot is now avaliable.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has finish own job, currently robot is now avaliable.',
            'code': 204
        })
    elif robot.status == 'available' and status == 'maintain':
        robot.status = 'maintain'  
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From avaliable to {robot.status}", f'Robot has maintain, currently robot is maintain.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has maintain, currently robot is maintain.',
            'code': 205
        })
    elif robot.status == 'maintain' and status == 'available':
        robot.status = 'available'  
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From maintain to {robot.status}", f'Robot has finish maintain, currently robot is now avaliable.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has finish maintain, currently robot is now avaliable.',
            'code': 202
        })
    elif robot.status == 'emergency' and status == 'available':
        if (robot.previous_status =='working'):
           robot.status = "wait_robot"
        else:
            robot.status = robot.previous_status
        robot.previous_status = None

        log_action(robot_id,f"From maintain to {robot.status}", f'Robot has finish maintain, currently robot is now avaliable.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has finish maintain, currently robot is now avaliable.',
            'code': 202
        })
    elif robot.status == 'available' and status == 'cancleall':
        robot.status = 'available'  

        log_action(robot_id,f"go to {robot.status}", f'Robot has cancleall, currently robot is available.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has cancleall, currently robot is available.',
            'code': 210
        })

    elif status == 'emergency':
        robot.previous_status = previous_status
        robot.status = 'emergency'  

        log_action(robot_id,f"go to {robot.status}", f'Robot has emergency, currently robot is emergency.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has emergency, currently robot is emergency.',
            'code': 210
        })
    elif status == 'pause':
        robot.previous_status = previous_status
        robot.status = 'pause'  

        log_action(robot_id,f"go to {robot.status}", f'Robot has pause, currently robot is pause.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has pause, currently robot is pause.',
            'code': 210
        })
    elif status == 'resume':
        robot.status = robot.previous_status
        robot.previous_status = None 

        log_action(robot_id,f"go to {robot.status}", f'Robot has resume, currently robot is resume.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has resume, currently robot is resume.',
            'code': 210
        })
    elif status == 'charging':
        robot.previous_status = previous_status
        robot.status = 'charging'  

        log_action(robot_id,f"go to {robot.status}", f'Robot has charging, currently robot is charging.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has charging, currently robot is charging.',
            'code': 210
        })
    elif status == 'manualcharging':
        robot.previous_status = previous_status
        robot.status = 'manualcharging'  

        log_action(robot_id,f"go to {robot.status}", f'Robot has manualcharging, currently robot is manualcharging.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has manualcharging, currently robot is manualcharging.',
            'code': 210
        })
    elif robot.status == 'available' and status == 'notcharge' :
        robot.status = 'available'
        robot.previous_status = None 

        log_action(robot_id,f"go to {robot.status}", f'Robot has notcharge, currently robot is available.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has notcharge, currently robot is available.',
            'code': 204
        })
        
    elif robot.status == 'working' and status == 'notcharge' :
        robot.status = 'working'
        robot.previous_status = None 

        log_action(robot_id,f"go to {robot.status}", f'Robot has notcharge, currently robot is working.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has notcharge, currently robot is working.',
            'code': 204
        })
        
    elif robot.status == 'manualcharging' and status == 'notcharge' :
        robot.status = 'available'
        robot.previous_status = None 

        log_action(robot_id,f"go to {robot.status}", f'Robot has notcharge, currently robot is available.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has notcharge, currently robot is available.',
            'code': 204
        })    
    elif robot.status == 'charging' and status == 'busy':
        robot.status = 'busy'  
        robot.destination = None
        robot.properties = None

        log_action(robot_id,f"From avaliable to {robot.status}", f'Robot has own job, currently robot is now busy.')
        db.session.commit()

        emit('status_updated', {
            'message': f'Robot {robot_id} has own job, currently robot is now busy.',
            'code': 203
        })
    else:
        emit('error', {'message': f'Unexpected status update for robot {robot_id} ,{robot.status} recived ,{status}',
            'code': 500
            })

def canclealljob(robot_id,state='other'):

    robot = Robot.query.filter_by(robot_id=robot_id).first()
    if not robot:
        emit('error', {'message': 'Robot not found'})
        return

    robot.status = 'available' 
    robot.pickup_id = None
    robot.destination = None
    robot.properties = None
    db.session.commit()
    job = RobotJobQueue.query.filter_by(assignedto=robot_id,status='processing').first()

    if not job:
        emit('error', {'message': f'No processing job found for robot {robot_id}'})
        return

    job.status = 'incompleted'
    job.destination_id = None
    # job.properties = None

    if(state == "working"):
        try:
            properties = json.loads(job.properties)
            assign_data = {
                "message": "Cancel Transfer",
                "info": {
                        "lot_no": properties["ui"]["lot_no"],
                        "status": "E",
                        "from_stocker": properties["ui"]["from_stocker"],
                        "from_level": properties["ui"]["from_level"],
                        "from_block": properties["ui"]["from_block"],
                        "to_stocker": properties["ui"]["to_stocker"],
                        "to_level": properties["ui"]["to_level"],
                        "to_block": properties["ui"]["to_block"],
                        "assigned_to": job.assignedto,
                        "job_no": job.id
                    }
                }

            assign_destination_url = POST_STATE  # เปลี่ยนเป็น URL จริง
            if(POST_STATE_ON):
                response = requests.post(assign_destination_url, json=assign_data)
                
        except Exception as e:
            pass

    # ✅ ถ้ามี Parent Job → เปลี่ยนสถานะเป็น completed ด้วย
    parent_job = None

    if job.parent_job_id:
        parent_job = db.session.get(RobotJobQueue, job.parent_job_id)
        if parent_job and parent_job.status != 'completed':
            parent_job.status = 'incompleted'
            parent_job.destination_id = None
            parent_job.parent_job_id = None
            log_action(robot_id, "Parent job incompleted", f"Parent job {parent_job.id} is now incompleted.")

    # ✅ ถ้ามี Child Job → เปลี่ยนสถานะเป็น completed ด้วย
    child_jobs = RobotJobQueue.query.filter_by(parent_job_id=job.id, status='processing').all()
    for child in child_jobs:
        child.status = 'incompleted'
        child.destination_id = None
        child.parent_job_id = None
        log_action(robot_id, "Child job incompleted", f"Child job {child.id} is now incompleted.")

    log_action(robot_id,f"From working to {robot.status}", f'Robot has incompleted {job.destination_name} at the task {job.id}, currently robot is now available.')

    
    db.session.commit()



    emit('status_updated', {
        'message': f'Robot {robot_id} has incompleted {job.destination_name} at the task {job.id}, currently robot is now available',
        'code': 202
    })