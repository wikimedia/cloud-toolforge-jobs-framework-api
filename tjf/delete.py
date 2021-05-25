from flask_restful import Resource, Api
from common.k8sclient import KubectlClient
from tjf.user import User

class Delete(Resource):
    def delete(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: use k8s API
        # TODO: proper error reporting, validation, etc
        # TODO: only delete objects create by this framework, use labels
        # TODO: support for cronjobs and replicationcontrollers
        return KubectlClient.kubectl("delete job {}".format(name), content=None)
