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
