# Copyright (C) 2022 Arturo Borrero Gonzalez <aborrero@wikimedia.org>
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

import yaml
from tjf.user import User
from flask_restful import Resource

# The ConfigMap is only read at startup. Restart the webservice to reload the available images
CONFIGMAP_FILE = "/etc/images.yaml"
AVAILABLE_IMAGES = []


def update_available_images():
    with open(CONFIGMAP_FILE) as f:
        yaml_data = yaml.safe_load(f.read())

    for i in yaml_data:
        shortname = i["shortname"]
        image = i["image"]

        entry = {"shortname": shortname, "image": image}

        print(f"Adding available image: {entry}")
        AVAILABLE_IMAGES.append(entry)

    if len(AVAILABLE_IMAGES) < 1:
        raise Exception("Empty list of available images")


def image_get_url(shortname):
    for image in AVAILABLE_IMAGES:
        if image.get("shortname") == shortname:
            return image.get("image")


def image_validate(shortname):
    if image_get_url(shortname) is not None:
        return True
    return False


def image_get_shortname(image: str) -> str:
    for i in AVAILABLE_IMAGES:
        if i.get("image") == image:
            return i.get("shortname")

    # this is only called in the k8s --> user path. If the job was created in the past we may
    # no longer have the image available for us. Print something to indicate that.
    return "unknown"


class Images(Resource):
    def get(self):
        try:
            user = User.from_request()  # noqa:F841
        except Exception as e:
            return f"Exception: {e}", 401

        return AVAILABLE_IMAGES


# TODO: remove this after a compat period
class Containers(Resource):
    def get(self):
        try:
            user = User.from_request()  # noqa:F841
        except Exception as e:
            return f"Exception: {e}", 401

        return AVAILABLE_IMAGES
