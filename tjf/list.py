from flask_restful import Resource, Api
from common.k8sclient import KubectlClient
import tjf.utils as utils
from tjf.job import Job
import yaml

def build_job_list(dict):
    job_list = []
    # multiple jobs defined?
    list = utils.dict_get_object(dict, "items")
    if list is not None:
        for job_definition in list:
            job = Job.from_k8s_object(job_definition)
            job_list.append(job)
    else:
        # single job defined?
        job = Job.from_k8s_object(dict)
        job_list.append(job)

    return job_list

class List(Resource):
    def get(self):
        output = KubectlClient.kubectl("get jobs -o yaml", content=None)
        #output = open("tjf/job.yaml", "r").read()
        dict = yaml.load(output)
        job_list = build_job_list(dict)

        return [j.get_api_object() for j in job_list]
