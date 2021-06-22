from flask_restful import Resource
from tjf.user import User
from tjf.ops import delete_job


class Delete(Resource):
    def delete(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        delete_job(user=user, jobname=name)
        return "", 200
