from flask_restful import Resource
from tjf.user import User
from tjf.job import delete_job


class Flush(Resource):
    def delete(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        delete_job(user=user, jobname=None)
        return "", 200
