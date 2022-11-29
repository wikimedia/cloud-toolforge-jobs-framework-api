# Copyright (C) 2021 Arturo Borrero Gonzalez <aborrero@wikimedia.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import json
import requests
from tjf.job import Job
from flask_restful import Resource, reqparse
from tjf.images import image_by_name, image_get_url
from tjf.user import User
from tjf.ops import find_job, create_job
from tjf.command import Command

# arguments that the API understands
parser = reqparse.RequestParser()
parser.add_argument("cmd", required=True)
parser.add_argument("imagename", required=True)
parser.add_argument("schedule")
parser.add_argument("continuous", type=bool, default=False)
parser.add_argument("name", required=True)
parser.add_argument("filelog", type=bool, default=False)
parser.add_argument("filelog_stdout", type=str, required=False)
parser.add_argument("filelog_stderr", type=str, required=False)
parser.add_argument("retry", choices=[0, 1, 2, 3, 4, 5], type=int, default=0)
parser.add_argument("memory")
parser.add_argument("cpu")
parser.add_argument("emails")


def _is_out_of_quota(e: requests.exceptions.HTTPError, job: Job, user: User) -> bool:
    """Returns True if the user is out of quota for a given job type."""
    if e.response.status_code != 403:
        return False
    if not str(e).startswith("403 Client Error: Forbidden for url"):
        return False

    resource_quota = user.kapi.get_objects("resourcequotas")[0]

    if job.k8s_type == "cronjobs":
        quota = resource_quota["status"]["hard"]["count/cronjobs.batch"]
        used = resource_quota["status"]["used"]["count/cronjobs.batch"]
    elif job.k8s_type == "deployments":
        quota = resource_quota["status"]["hard"]["count/deployments.apps"]
        used = resource_quota["status"]["used"]["count/deployments.apps"]
    elif job.k8s_type == "jobs":
        quota = resource_quota["status"]["hard"]["count/jobs.batch"]
        used = resource_quota["status"]["used"]["count/jobs.batch"]
    else:
        return False

    if used >= quota:
        return True

    return False


def _handle_k8s_exception(e: requests.exceptions.HTTPError, job: Job, user: User):
    """Function to handle some known kubernetes API exceptions."""
    if _is_out_of_quota(e, job, user):
        hint_url = "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Jobs_framework#Job_quotas"
        result = f"HTTP 403: out of quota for this kind of job. Please check {hint_url}", 403
        return result

    json_s = json.dumps(job.get_k8s_object()).encode("utf-8").decode("unicode-escape")

    # hope k8s doesn't change this behavior too often
    if e.response.status_code == 409 or str(e).startswith("409 Client Error: Conflict for url"):
        result = "HTTP 409: an object with the same name exists already", 409
    elif e.response.status_code == 422 or str(e).startswith(
        "422 Client Error: Unprocessable Entity for url"
    ):
        if job.k8s_type == "cronjobs":
            result = f"HTTP 422: likely wrong schedule time. k8s JSON: {json_s}", 422
        else:
            result = f"HTTP 422: likely an internal bug. k8s JSON: {json_s}", 422
    else:
        result = (
            f"HTTP {e.response.status_code}: likely an internal bug: {str(e)}. k8s JSON: {json_s}",
            e.response.status_code,
        )

    return result


class Run(Resource):
    def post(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        args = parser.parse_args()

        if not image_by_name(args.imagename):
            return "HTTP 400: invalid container image", 400

        if find_job(user=user, jobname=args.name) is not None:
            return "HTTP 409: a job with the same name exists already", 409

        command = Command.from_api(
            args.cmd, args.filelog, args.filelog_stdout, args.filelog_stderr, args.name
        )

        try:
            job = Job(
                command=command,
                image=image_get_url(args.imagename),
                jobname=args.name,
                ns=user.namespace,
                username=user.name,
                schedule=args.schedule,
                cont=args.continuous,
                k8s_object=None,
                retry=args.retry,
                memory=args.memory,
                cpu=args.cpu,
                emails=args.emails,
            )

            result = create_job(user=user, job=job)
        except requests.exceptions.HTTPError as e:
            result = _handle_k8s_exception(e, job, user)
        except Exception as e:
            result = f"ERROR: {str(e)}", 400
        return result
