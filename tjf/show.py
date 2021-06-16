from flask_restful import Resource
from tjf.job import find_job
from tjf.user import User


class Show(Resource):
    def get(self, name):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        job = find_job(user=user, jobname=name)
        if job:
            return job.get_api_object()

        if not job:
            return {}, 404
