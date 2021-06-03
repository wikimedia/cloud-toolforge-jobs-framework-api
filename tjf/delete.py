from flask_restful import Resource, Api
from tjf.user import User
from tjf.job import Job


class Delete(Resource):
    def delete(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        # TODO: proper error reporting, validation, etc
        # TODO: only delete objects create by this framework, use labels
        # TODO: support for replicationcontrollers
        user.kapi.delete_objects("jobs", selector=Job.get_labels_selector(name, user.name))
        user.kapi.delete_objects("cronjobs", selector=Job.get_labels_selector(name, user.name))
