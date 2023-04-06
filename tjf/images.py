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

from dataclasses import dataclass
from typing import List, Optional

import yaml
from flask_restful import Resource

from common.k8sclient import K8sClient
from tjf.user import User


@dataclass(frozen=True)
class Image:
    canonical_name: str
    aliases: List[str]
    container: str
    state: str


# The ConfigMap is only read at startup. Restart the webservice to reload the available images
AVAILABLE_IMAGES: List[Image] = []


VARIANT_KEY = "jobs-framework"
# TODO: make configurable
CONTAINER_TAG = "latest"


def update_available_images():
    client = K8sClient.from_container_service_account(namespace="tf-public")
    configmap = client.get_object("configmaps", "image-config")
    yaml_data = yaml.safe_load(configmap["data"]["images-v1.yaml"])

    AVAILABLE_IMAGES.clear()

    for name, data in yaml_data.items():
        if VARIANT_KEY not in data["variants"]:
            continue

        container = data["variants"][VARIANT_KEY]["image"]
        image = Image(
            canonical_name=name,
            aliases=data.get("aliases", []),
            container=f"{container}:{CONTAINER_TAG}",
            state=data["state"],
        )

        AVAILABLE_IMAGES.append(image)

    if len(AVAILABLE_IMAGES) < 1:
        raise Exception("Empty list of available images")


def image_by_name(name: str) -> Optional[Image]:
    for image in AVAILABLE_IMAGES:
        if image.canonical_name == name or name in image.aliases:
            return image
    return None


def image_by_container_url(url: str) -> Optional[Image]:
    for image in AVAILABLE_IMAGES:
        if image.container == url:
            return image
    return None


def image_get_url(name: str) -> str:
    image = image_by_name(name)
    if not image:
        raise Exception(f"No such image {image}")

    return image.container


class Images(Resource):
    def get(self):
        user = User.from_request()  # noqa:F841

        return [
            {
                "shortname": image.canonical_name,
                "image": image.container,
            }
            for image in AVAILABLE_IMAGES
            if image.state == "stable"
        ]
