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

import requests
from tjf.job import Job
from flask_restful import Resource, reqparse
from tjf.containers import container_validate, container_get_image
from tjf.user import User
from tjf.ops import find_job, create_job

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
            cont=args.continuous,
            k8s_object=None,
        )

        try:
            result = create_job(user=user, job=job)
        except requests.exceptions.HTTPError as e:
            # hope k8s doesn't change this behavior too often
            if e.response.status_code == 409 or str(e).startswith(
                "409 Client Error: Conflict for url"
            ):
                result = "HTTP 409: an object with the same name exists already", 409
            elif e.response.status_code == 422 or str(e).startswith(
                "422 Client Error: Unprocessable Entity for url"
            ):
                result = "HTTP 422: wrong schedule time", 422
            else:
                result = str(e), e.response.status_code

        return result
