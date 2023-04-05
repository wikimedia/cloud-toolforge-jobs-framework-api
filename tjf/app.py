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

from flask import Flask
from flask_restful import Api
from tjf.healthz import Healthz
from tjf.metrics import metrics_init_app
from tjf.run import Run
from tjf.show import Show
from tjf.list import List
from tjf.delete import Delete
from tjf.restart import Restart
from tjf.flush import Flush
from tjf.images import Images, update_available_images


def create_app(*, load_images=True):
    app = Flask(__name__)
    api = Api(app)

    metrics_init_app(app)

    api.add_resource(Healthz, "/healthz")
    api.add_resource(Run, "/api/v1/run/")
    api.add_resource(Show, "/api/v1/show/<name>")
    api.add_resource(List, "/api/v1/list/")
    api.add_resource(Delete, "/api/v1/delete/<name>")
    api.add_resource(Restart, "/api/v1/restart/<name>")
    api.add_resource(Flush, "/api/v1/flush/")
    api.add_resource(Images, "/api/v1/images/")

    if load_images:
        # before app startup!
        update_available_images()

    return app