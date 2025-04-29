from flask_socketio import SocketIO, emit
from models.robot import Robot
from models.destination import Destination


def handle_call_robot(data):
    robot_id = data['robot_id']
    # ดึงหุ่นยนต์ทั้งหมดที่มีสถานะ 'wait_robot'
    robots = Robot.query.filter(Robot.robot_id == robot_id, Robot.status.in_(["wait_robot", "NeedCharge"])).all()

    # print(robots)

    if not robots:
        # print('No robots in wait_robot status')
        emit('call_roboted', {'message': 'No robots in wait_robot status','code':200})
        return
    listrobot = {}
    # วนลูปผ่านหุ่นยนต์ที่มีสถานะ 'wait_robot'
    for robot in robots:
        destination = Destination.query.filter_by(id=robot.destination_id).first()
        pickup = Destination.query.filter_by(id=robot.pickup_id).first()
        # print(destination)
        # print(pickup)
        if pickup and (destination == None):
            listrobot = {
                'robot_id': robot.robot_id,
                'destination_id': pickup.id,
                'destination_name': pickup.name,
                'properties': robot.properties
            }
        elif destination and (pickup == None):
            listrobot = {
                'robot_id': robot.robot_id,
                'destination_id': destination.id,
                'destination_name': destination.name,
                'properties': robot.properties
            }
        else:
            listrobot = {
                'robot_id': robot.robot_id,
                'destination_id': destination.id,
                'destination_name': destination.name,
                'pickup_name' : pickup.name,
                'pickup_id': pickup.id,
                'properties': robot.properties
            }
        
        
    # ส่งข้อมูลหุ่นยนต์ที่มีสถานะ 'wait_robot' กลับไป
    # print(listrobot)
    emit('call_roboted', {'robots': listrobot,'code':202})