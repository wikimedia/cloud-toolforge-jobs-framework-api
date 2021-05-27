from flask_restful import Resource, Api
from common.k8sclient import KubectlClient
from tjf.user import User

class Flush(Resource):
    def delete(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: use labels to only delete stuff created by this framework
        user.kapi.delete_objects("jobs")
        user.kapi.delete_objects("cronjobs")
        user.kapi.delete_objects("replicationcontrollers")

        return "", 200
