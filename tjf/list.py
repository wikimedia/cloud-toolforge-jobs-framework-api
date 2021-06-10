from flask_restful import Resource
from tjf.user import User
from tjf.job import Job


class List(Resource):
    def get(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        selector = Job.get_labels_selector(jobname=None, username=user.name)

        job_list = []
        for job in user.kapi.get_objects("jobs", selector=selector):
            job_list.append(Job.from_job_k8s_object(job))

        for job in user.kapi.get_objects("cronjobs", selector=selector):
            job_list.append(Job.from_cronjob_k8s_object(job))

        for job in user.kapi.get_objects("deployments", selector=selector):
            job_list.append(Job.from_dp_k8s_object(job))

        return [j.get_api_object() for j in job_list]
