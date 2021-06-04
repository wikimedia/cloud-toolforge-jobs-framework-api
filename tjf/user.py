import os
import yaml
from flask import request
from common.k8sclient import K8sClient


class User:
    def __init__(self, name):
        self.name = name
        self.namespace = f"tool-{self.name}"

        # TODO: fetch this from LDAP instead?
        self.home = f"/data/project/{name}"

        self.kubeconfig_path = os.path.join(self.home, ".kube", "config")
        self.validate_kubeconfig()
        self.kapi = K8sClient.from_file(filename=self.kubeconfig_path)

    def validate_kubeconfig(self):
        path = self.kubeconfig_path

        try:
            with open(path) as file:
                config = yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"couldn't read kubeconfig for user '{self.name}': {e}")

        if config is None:
            raise Exception(f"user file '{path}' is empty")

        # copied from maintain_kubeusers :-P
        if all(
            k in config
            for k in (
                "apiVersion",
                "kind",
                "clusters",
                "users",
                "contexts",
                "current-context",
            )
        ):
            return config
        else:
            raise Exception(f"invalid kubeconfig for user '{self.name}'")

    @classmethod
    def from_request(self):
        header = "ssl-client-subject-dn"
        if header not in request.headers:
            raise Exception(f"missing '{header}' header")

        value = request.headers.get(header)
        if not value.startswith("CN="):
            raise Exception(f"missing CN= string in '{header}' header")

        name = value.split("=")[1]

        return User(name=name)
