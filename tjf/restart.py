from flask_restful import Resource
from tjf.user import User
from tjf.ops import find_job, restart_job


class Restart(Resource):
    def post(self, name):
        user = User.from_request()

        job = find_job(user=user, jobname=name)
        if not job:
            return {}, 404

        try:
            restart_job(user=user, job=job)
        except Exception as e:
            return f"ERROR: {e}", 400

        return "", 200
