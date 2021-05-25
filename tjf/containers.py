from tjf.user import User
from flask_restful import Resource, Api

# We could maintain this harcoded list by hand, similar to what we do for tools-webservices
AVAILABLE_CONTAINERS = [
    {"type": "toolforge-stretch-sssd"},
    {"type": "toolforge-buster-sssd"},
    {"type": "toolforge-bullseye-sssd"},
]


def validate_container_type(type):
    for container_type in AVAILABLE_CONTAINERS:
        if container_type.get("type") == type:
            return True
    return False


class Containers(Resource):
    def get(self):
        try:
            user = User.from_request()
        except Exception as e:
            return f"Exception: {e}", 401

        return AVAILABLE_CONTAINERS
