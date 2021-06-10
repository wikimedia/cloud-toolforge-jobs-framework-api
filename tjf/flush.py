from flask_restful import Resource
from tjf.user import User
from tjf.job import Job


class Flush(Resource):
    def delete(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        user.kapi.delete_objects(
            "jobs", selector=Job.get_labels_selector(jobname=None, username=user.name)
        )
        user.kapi.delete_objects(
            "cronjobs", selector=Job.get_labels_selector(jobname=None, username=user.name)
        )
        user.kapi.delete_objects(
            "deployments", selector=Job.get_labels_selector(jobname=None, username=user.name)
        )
        user.kapi.delete_objects(
            "pods", selector=Job.get_labels_selector(jobname=None, username=user.name)
        )

        return "", 200
