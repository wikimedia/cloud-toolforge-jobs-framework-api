from flask_restful import Resource, Api
from tjf.user import User
import tjf.utils as utils
from tjf.job import Job


class List(Resource):
    def get(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        job_list = []
        for job in user.kapi.get_objects("jobs"):
            job_list.append(Job.from_job_k8s_object(job))

        for job in user.kapi.get_objects("cronjobs"):
            job_list.append(Job.from_cronjob_k8s_object(job))

        return [j.get_api_object() for j in job_list]
