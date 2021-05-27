from tjf.user import User
from flask_restful import Resource, Api

# We could maintain this harcoded list by hand, similar to what we do for tools-webservices
AVAILABLE_CONTAINERS = [
    {
        "name": "tf-buster",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-sssd:latest",
    },
    {
        "name": "tf-buster-std",
        "type": "docker-registry.tools.wmflabs.org/toolforge-buster-standalone:latest",
    },
]


def container_get_image(name):
    for container in AVAILABLE_CONTAINERS:
        if container.get("name") == name:
            return container.get("type")


def container_validate(name):
    for container in AVAILABLE_CONTAINERS:
        if container.get("name") == name:
            return True
    return False


class Containers(Resource):
    def get(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        return AVAILABLE_CONTAINERS
