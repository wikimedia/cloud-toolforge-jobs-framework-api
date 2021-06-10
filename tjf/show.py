from flask_restful import Resource
from tjf.job import Job
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

        selector = Job.get_labels_selector(jobname=None, username=user.name)

        job_list = []
        for job in user.kapi.get_objects("jobs", selector=selector):
            job_list.append(Job.from_job_k8s_object(job))

        for job in user.kapi.get_objects("cronjobs", selector=selector):
            job_list.append(Job.from_cronjob_k8s_object(job))

        for job in user.kapi.get_objects("deployments", selector=selector):
            job_list.append(Job.from_dp_k8s_object(job))

        job = find_job(job_list, name)
        # we found the job
        if job:
            return job.get_api_object()

        if not job:
            return {}, 404
