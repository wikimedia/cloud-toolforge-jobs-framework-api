from flask_restful import Resource, Api
from common.k8sclient import KubectlClient
from tjf.job import Job
import tjf.utils as utils
import yaml
from tjf.user import User

def find_job(dict, name):
    # multiple jobs defined?
    list = utils.dict_get_object(dict, "items")
    if list is not None:
        for job_definition in list:
            job = Job.from_k8s_object(job_definition)
            if job.jobname == name:
                return job
    # single job defined?
    job = Job.from_k8s_object(dict)
    if job.jobname == name:
        return job


class Show(Resource):
    def get(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: figure this out from the client TLS cert
        ns = "tools-test"
        username = "test"

        # get and search Jobs objects
        output = KubectlClient.kubectl("get jobs -o yaml", content=None)
        #output = open("tjf/job.yaml", "r").read()
        dict = yaml.load(output)
        job = find_job(dict, name)
        # we found the job
        if job:
            return job.get_api_object()

        # TODO: also get and search CronJob objects
        # TODO: also get and search ReplicationController objects

        if not job:
            return {}, 404
