from flask_restful import Resource, Api
from common.k8sclient import KubectlClient
from tjf.user import User

class Flush(Resource):
    def delete(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: figure out namespace from client TLS cert
        # TODO: replace kubectl call with proper k8sclient usage
        # TODO: use labels to only delete jobs created by this framework
        KubectlClient.kubectl("delete job --all", content=None)
        KubectlClient.kubectl("delete cronjob --all", content=None)
        KubectlClient.kubectl("delete replicationcontroller --all", content=None)
