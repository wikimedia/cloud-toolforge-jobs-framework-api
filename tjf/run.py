import requests
from tjf.job import Job, find_job
from flask_restful import Resource, reqparse
from tjf.containers import container_validate, container_get_image
from tjf.user import User

# arguments that the API understands
parser = reqparse.RequestParser()
parser.add_argument("cmd")
parser.add_argument("imagename")
parser.add_argument("schedule")
parser.add_argument("continuous", type=bool, default=False)
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

        if find_job(user=user, jobname=args.name) is not None:
            return "HTTP 409: a job with the same name exists already", 409

        job = Job(
            cmd=args.cmd,
            image=container_get_image(args.imagename),
            jobname=args.name,
            ns=user.namespace,
            username=user.name,
            schedule=args.schedule,
            status=None,
            cont=args.continuous,
        )

        try:
            result = user.kapi.create_object(job.k8s_type, job.get_k8s_object())
        except requests.exceptions.HTTPError as e:
            # hope k8s doesn't change this behavior too often
            if e.response.status_code == 409 or str(e).startswith(
                "409 Client Error: Conflict for url"
            ):
                result = "HTTP 409: an object with the same name exists already", 409
            else:
                result = str(e), e.response.status_code

        return result
