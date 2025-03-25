from flask_restful import Resource
from models.robot_job import RobotJobQueue

class JobQueueStatus(Resource):
    def get(self):
        jobs = RobotJobQueue.query.all()
        job_list = [{
            'job_id': job.id,
            'job_description': job.job_description,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'assigned_to': job.assignedto,
            'properties': job.properties
        } for job in jobs]

        return {'job_queue': job_list}, 200
