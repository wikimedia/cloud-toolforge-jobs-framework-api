from flask_restful import Resource
from tjf.user import User
from tjf.ops import list_all_jobs


class List(Resource):
    def get(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        job_list = list_all_jobs(user=user, jobname=None)
        return [j.get_api_object() for j in job_list]
