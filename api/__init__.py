from flask_restful import Api
from .jobqueuestatus import JobQueueStatus
from .robotstatus_api import RobotStatus
from .adddestination_api import AddDestination
from .robotcorrdinates_api import RobotCoordinates
from .availablerobots_api import AvailableRobots
from .assigndestination_api import AssignDestination
from .updatedestination_api import UpdateDestination
from .jobtoqueue_api import JobToQueue
from .posttask_api import PostTask

api = Api()

# ✅ เพิ่ม Resource API
api.add_resource(RobotStatus, '/robot/<string:robot_id>/status')
api.add_resource(RobotCoordinates, '/robot/<string:robot_id>/coordinates')
api.add_resource(AvailableRobots, '/robots/available')
api.add_resource(AssignDestination, '/assign/destination')
api.add_resource(UpdateDestination,'/update/destination/<int:destination_id>')
api.add_resource(AddDestination, '/destination')
api.add_resource(JobQueueStatus, '/job/queue/status') 
api.add_resource(JobToQueue, '/job/queue') 
api.add_resource(PostTask,'/sony/job')
