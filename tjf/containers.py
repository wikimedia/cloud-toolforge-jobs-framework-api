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
from tjf.user import User
from flask_restful import Resource

# We could maintain this harcoded list by hand, similar to what we do for tools-webservices
# or we could store this information in a kubernetes configmap, or kind of a middle ground:
# fetch containers from our docker registry an generate the list at startup time.
# This could enable a kind of simple workflow: restart the API to reload the available containers.

BASE_FQDN = "docker-registry.tools.wmflabs.org"
BASE_URL = f"https://{BASE_FQDN}"
CATALOG_URL = f"{BASE_URL}/v2/_catalog"

AVAILABLE_CONTAINERS = []


def image_is_interesting(imagename: str):
    if imagename.startswith("wikimedia-"):
        # example: 'wikimedia-buster'
        return True
    if imagename.startswith("toolforge-"):
        if imagename.endswith("sssd-base"):
            # example: 'toolforge-php73-sssd-base'
            return True
        if imagename.endswith("standalone"):
            # example: 'toolforge-buster-standalone'
            return True

    return False


def update_available_containers():
    # let this raise an exception if something wrongs happens
    r = requests.get(CATALOG_URL)
    r.raise_for_status()

    catalog = r.json()
    if catalog.get("repositories") is None:
        raise Exception("Couldn't understand the catalog format")

    for image in catalog.get("repositories"):
        if not image_is_interesting(image):
            # not interested in this image
            continue

        shortname = (
            image.replace("toolforge-", "tf-")
            .replace("-standalone", "-std")
            .replace("-sssd-base", "")
            .replace("wikimedia-", "wm-")
        )
        image = f"{BASE_FQDN}/{image}:latest"

        entry = {"shortname": shortname, "image": image}

        print(f"Adding available container: {entry}")
        AVAILABLE_CONTAINERS.append(entry)

    if len(AVAILABLE_CONTAINERS) < 1:
        raise Exception(f"Couldn't generate available containers from {CATALOG_URL}")


def container_get_image(shortname):
    for container in AVAILABLE_CONTAINERS:
        if container.get("shortname") == shortname:
            return container.get("image")


def container_validate(shortname):
    if container_get_image(shortname) is not None:
        return True
    return False


def container_get_shortname(image):
    for container in AVAILABLE_CONTAINERS:
        if container.get("image") == image:
            return container.get("shortname")


class Containers(Resource):
    def get(self):
        try:
            user = User.from_request()  # noqa:F841
        except Exception as e:
            return f"Exception: {e}", 401

        return AVAILABLE_CONTAINERS
