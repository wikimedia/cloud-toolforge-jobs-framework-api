from flask_restful import Resource, Api
from common.k8sclient import KubectlClient

class Delete(Resource):
    def delete(self, name):
        # TODO: use k8s API
        # TODO: proper error reporting, validation, etc
        # TODO: only delete objects create by this framework, use labels
        # TODO: support for cronjobs and replicationcontrollers
        return KubectlClient.kubectl("delete job {}".format(name), content=None)
