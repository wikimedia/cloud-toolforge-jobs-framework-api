# Copyright (C) 2021 Arturo Borrero Gonzalez <aborrero@wikimedia.org>
# Copyright (C) 2023 Taavi Väänänen <hi@taavi.wtf>
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
from tjf.error import TjfError, TjfValidationError

from tjf.job import Job
from tjf.user import User


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


def create_error_from_k8s_response(
    e: requests.exceptions.HTTPError, job: Job, user: User
) -> TjfError:
    """Function to handle some known kubernetes API exceptions."""
    error_data = {
        "k8s_object": job.get_k8s_object(),
        "k8s_error": {"status_code": e.response.status_code, "body": e.response.text},
    }

    if _is_out_of_quota(e, job, user):
        return TjfValidationError(
            "Out of quota for this kind of job. Please see https://w.wiki/6YLP for details.",
            data=error_data,
        )

    # hope k8s doesn't change this behavior too often
    if e.response.status_code == 409 or str(e).startswith("409 Client Error: Conflict for url"):
        return TjfValidationError(
            "An object with the same name exists already", http_status_code=409, data=error_data
        )

    return TjfError(
        "Failed to create a job, likely an internal bug in the jobs framework.", data=error_data
    )
