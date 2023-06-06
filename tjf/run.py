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

from tjf.cron import CronExpression, CronParsingError
from tjf.error import TjfError, TjfValidationError
from tjf.job import Job
from flask_restful import Resource, reqparse
from tjf.images import image_by_name
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


class Run(Resource):
    def post(self):
        user = User.from_request()

        args = parser.parse_args()
        image = image_by_name(args.imagename)

        if not image:
            raise TjfValidationError(f"No such image '{args.imagename}'")

        if find_job(user=user, jobname=args.name) is not None:
            raise TjfValidationError(
                "A job with the same name exists already", http_status_code=409
            )

        if args.filelog and not image.type.supports_file_logs():
            raise TjfValidationError("Buildpack images do not support file logs")

        command = Command.from_api(
            user_command=args.cmd,
            use_wrapper=image.type.use_command_wrapper(),
            filelog=args.filelog,
            filelog_stdout=args.filelog_stdout,
            filelog_stderr=args.filelog_stderr,
            jobname=args.name,
        )

        if args.schedule:
            try:
                schedule = CronExpression.parse(args.schedule, f"{user.namespace} {args.name}")
            except CronParsingError as e:
                raise TjfValidationError(
                    f"Unable to parse cron expression '{args.schedule}'"
                ) from e
        else:
            schedule = None

        try:
            job = Job(
                command=command,
                image=image,
                jobname=args.name,
                ns=user.namespace,
                username=user.name,
                schedule=schedule,
                cont=args.continuous,
                k8s_object=None,
                retry=args.retry,
                memory=args.memory,
                cpu=args.cpu,
                emails=args.emails,
            )

            result = create_job(user=user, job=job)
        except TjfError as e:
            raise e
        except Exception as e:
            raise TjfError("Unable to start job") from e
        return result
