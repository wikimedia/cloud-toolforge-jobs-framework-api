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

import functools
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import requests
import urllib.parse
import yaml
from flask_restful import Resource
from toolforge_weld.kubernetes import K8sClient
from toolforge_weld.kubernetes_config import Kubeconfig

from tjf.error import TjfError
from tjf.user import User
from tjf.utils import USER_AGENT


LOGGER = logging.getLogger(__name__)


class ImageType(Enum):
    STANDARD = "standard"
    BUILDPACK = "buildpack"

    def use_command_wrapper(self) -> bool:
        """Check if the command using this image type should be executed via a shell wrapper."""
        return self != ImageType.BUILDPACK

    def supports_file_logs(self) -> bool:
        """Check if this image type supports file logs."""
        return self != ImageType.BUILDPACK

    def use_standard_nfs(self) -> bool:
        return self != ImageType.BUILDPACK


@dataclass(frozen=True)
class Image:
    type: ImageType
    canonical_name: str
    aliases: List[str]
    container: str
    state: str


@dataclass(frozen=True)
class HarborConfig:
    host: str


# The ConfigMap is only read at startup. Restart the webservice to reload the available images
AVAILABLE_IMAGES: List[Image] = []


CONFIG_VARIANT_KEY = "jobs-framework"
# TODO: make configurable
CONFIG_CONTAINER_TAG = "latest"

HARBOR_CONFIG_PATH = "/etc/jobs-api/harbor.json"
HARBOR_IMAGE_STATE = "stable"


def update_available_images():
    client = K8sClient(
        kubeconfig=Kubeconfig.from_container_service_account(namespace="tf-public"),
        user_agent=USER_AGENT,
    )
    configmap = client.get_object("configmaps", "image-config")
    yaml_data = yaml.safe_load(configmap["data"]["images-v1.yaml"])

    AVAILABLE_IMAGES.clear()

    for name, data in yaml_data.items():
        if CONFIG_VARIANT_KEY not in data["variants"]:
            continue

        container = data["variants"][CONFIG_VARIANT_KEY]["image"]
        image = Image(
            type=ImageType.STANDARD,
            canonical_name=name,
            aliases=data.get("aliases", []),
            container=f"{container}:{CONFIG_CONTAINER_TAG}",
            state=data["state"],
        )

        AVAILABLE_IMAGES.append(image)

    if len(AVAILABLE_IMAGES) < 1:
        raise TjfError("Empty list of available images")


@functools.lru_cache(maxsize=None)
def get_harbor_config() -> HarborConfig:
    with open(HARBOR_CONFIG_PATH, "r") as f:
        data = json.load(f)
    return HarborConfig(
        host=data["host"],
    )


def get_harbor_images_for_name(namespace: str, name: str) -> List[Image]:
    config = get_harbor_config()

    encoded_namespace = urllib.parse.quote_plus(namespace)
    encoded_name = urllib.parse.quote_plus(name)

    try:
        response = requests.get(
            f"https://{config.host}/api/v2.0/projects/{encoded_namespace}/repositories/{encoded_name}/artifacts",
            params={
                # TODO: pagination if needed
                "page": "1",
                "page_size": "25",
            },
            headers={
                "User-Agent": f"jobs-framework-api python-requests/{requests.__version__}",
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        LOGGER.warning("Failed to load Harbor tags for %s/%s", namespace, name, exc_info=True)
        return []

    images: List[Image] = []
    for artifact in response.json():
        if artifact["type"] != "IMAGE":
            continue
        if not artifact["tags"]:
            continue

        for tag in artifact["tags"]:
            tag_name = tag["name"]
            images.append(
                Image(
                    type=ImageType.BUILDPACK,
                    canonical_name=f"{namespace}/{name}:{tag_name}",
                    aliases=[],
                    container=f"{config.host}/{namespace}/{name}:{tag_name}",
                    state=HARBOR_IMAGE_STATE,
                )
            )

    return images


def get_harbor_images(namespace: str) -> List[Image]:
    config = get_harbor_config()

    encoded_namespace = urllib.parse.quote_plus(namespace)

    try:
        response = requests.get(
            f"https://{config.host}/api/v2.0/projects/{encoded_namespace}/repositories",
            params={
                "with_tag": "true",
                # TODO: pagination if needed
                "page": "1",
                "page_size": "25",
            },
            headers={
                "User-Agent": f"jobs-framework-api python-requests/{requests.__version__}",
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 401:
            # You seem to get a 401 when the namespace does not exist for whatever reason
            # don't log those, they are usually typos
            LOGGER.warning(
                "Failed to load Harbor images for namespace %s", namespace, exc_info=True
            )
        return []

    images: List[Image] = []

    for repository in response.json():
        name = repository["name"][len(namespace) + 1 :]
        images.extend(get_harbor_images_for_name(namespace, name))

    return images


def image_by_name(name: str) -> Optional[Image]:
    for image in AVAILABLE_IMAGES:
        if image.canonical_name == name or name in image.aliases:
            return image

    if "/" in name and ":" in name:
        # harbor image?
        namespace, image_name = name.split("/", 1)
        image_name, _ = image_name.split(":", 1)
        for image in get_harbor_images_for_name(namespace, image_name):
            if image.canonical_name == name:
                return image

    return None


def image_by_container_url(url: str) -> Optional[Image]:
    for image in AVAILABLE_IMAGES:
        if image.container == url:
            return image

    harbor_config = get_harbor_config()
    if url.startswith(harbor_config.host):
        # we assume images loaded from URLs exist

        image_name_with_tag = url[len(harbor_config.host) + 1 :]
        return Image(
            type=ImageType.BUILDPACK,
            canonical_name=image_name_with_tag,
            aliases=[],
            container=url,
            state=HARBOR_IMAGE_STATE,
        )

    return None


class Images(Resource):
    def get(self):
        user = User.from_request()

        images = AVAILABLE_IMAGES + get_harbor_images(user.namespace)

        return [
            {
                "shortname": image.canonical_name,
                "image": image.container,
            }
            for image in sorted(images, key=lambda image: image.canonical_name)
            if image.state == "stable"
        ]
