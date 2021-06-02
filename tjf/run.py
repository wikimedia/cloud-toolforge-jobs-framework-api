from tjf.job import Job
from flask_restful import Resource, Api, reqparse
from tjf.containers import container_validate, container_get_image
from tjf.user import User
import yaml
import sys

# arguments that the API understands
parser = reqparse.RequestParser()
parser.add_argument("cmd")
parser.add_argument("imagename")
parser.add_argument("schedule")
parser.add_argument("continuous")
parser.add_argument("name")


class Run(Resource):
    def post(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        args = parser.parse_args()

        if not container_validate(args.imagename):
            return "Invalid container type", 400

        # TODO: add support for schedule & continuous
        job = Job(
            args.cmd,
            container_get_image(args.imagename),
            args.name,
            user.namespace,
            user.name,
            status=None,
        )

        # TODO: add special error handling for 409: confict for URL
        # That means there is already a job with the same name
        return user.kapi.create_object("jobs", job.get_k8s_object())
