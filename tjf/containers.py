from tjf.user import User
from flask_restful import Resource

# We could maintain this harcoded list by hand, similar to what we do for tools-webservices
AVAILABLE_CONTAINERS = [
    {
        "shortname": "tf-buster",
        "image": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
    },
    {
        "shortname": "tf-buster-std",
        "image": "docker-registry.tools.wmflabs.org/toolforge-buster-standalone:latest",
    },
]


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
