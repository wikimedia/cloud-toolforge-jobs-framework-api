from flask_restful import Resource
from tjf.user import User
from tjf.ops import find_job, restart_job


class Restart(Resource):
    def post(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        job = find_job(user=user, jobname=name)
        if not job:
            return {}, 404

        restart_job(user=user, job=job)
        return "", 200
