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
from flask_restful import Resource
from tjf.error import TjfError
from tjf.user import User


class Quota(Resource):
    def get(self):
        user = User.from_request()

        resource_quota = user.kapi.get_object("resourcequotas", user.namespace)
        limit_range = user.kapi.get_object("limitranges", user.namespace)

        if not resource_quota or not limit_range:
            raise TjfError("Unable to load quota information for this tool")

        container_limit = next(
            limit for limit in limit_range["spec"]["limits"] if limit["type"] == "Container"
        )

        quota_data = {
            "categories": [
                {
                    "name": "Running jobs",
                    "items": [
                        {
                            "name": "Total running jobs at once (Kubernetes pods)",
                            "limit": int(resource_quota["status"]["hard"]["pods"]),
                            "used": int(resource_quota["status"]["used"]["pods"]),
                        },
                        {
                            "name": "Running one-off and cron jobs",
                            "limit": int(resource_quota["status"]["hard"]["count/jobs.batch"]),
                            "used": int(resource_quota["status"]["used"]["count/jobs.batch"]),
                        },
                        # Here we assume that for all CPU and RAM use, requests are set to half of
                        # what limits are set. This is true for at least jobs-api usage.
                        # TODO: somehow display if requests are using more than half of limits.
                        {
                            "name": "CPU",
                            "limit": resource_quota["status"]["hard"]["limits.cpu"],
                            "used": resource_quota["status"]["used"]["limits.cpu"],
                        },
                        {
                            "name": "Memory",
                            "limit": resource_quota["status"]["hard"]["limits.memory"],
                            "used": resource_quota["status"]["used"]["limits.memory"],
                        },
                    ],
                },
                {
                    "name": "Per-job limits",
                    "items": [
                        {
                            "name": "CPU",
                            "limit": container_limit["max"]["cpu"],
                        },
                        {
                            "name": "Memory",
                            "limit": container_limit["max"]["memory"],
                        },
                    ],
                },
                {
                    "name": "Job definitions",
                    "items": [
                        {
                            "name": "Cron jobs",
                            "limit": int(resource_quota["status"]["hard"]["count/cronjobs.batch"]),
                            "used": int(resource_quota["status"]["used"]["count/cronjobs.batch"]),
                        },
                        {
                            "name": "Continuous jobs (including web services)",
                            "limit": int(
                                resource_quota["status"]["hard"]["count/deployments.apps"]
                            ),
                            "used": int(
                                resource_quota["status"]["used"]["count/deployments.apps"]
                            ),
                        },
                    ],
                },
            ],
        }

        return quota_data, 200
