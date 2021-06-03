from flask_restful import Resource, Api
from tjf.job import Job
import tjf.utils as utils
import yaml
from tjf.user import User


def find_job(list, name):
    for job in list:
        if job.jobname == name:
            return job


class Show(Resource):
    def get(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: also get and search ReplicationController objects
        job_list = []
        for job in user.kapi.get_objects("jobs"):
            job_list.append(Job.from_job_k8s_object(job))

        for job in user.kapi.get_objects("cronjobs"):
            job_list.append(Job.from_cronjob_k8s_object(job))

        job = find_job(job_list, name)
        # we found the job
        if job:
            return job.get_api_object()

        if not job:
            return {}, 404
