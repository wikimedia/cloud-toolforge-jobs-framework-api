# from tools-webservice toolsws/backends/kubernetes.py
# Copyright (C) 2020 Bryan Davis <bd808@wikimedia.org>

import requests
import yaml
from typing import Optional

from tjf.error import TjfError


KUBERNETES_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _find_cfg_obj(config, kind, name):
    """Lookup a named object in a config."""
    for obj in config[kind]:
        if obj["name"] == name:
            return obj[kind[:-1]]
    raise TjfError("Key {} not found in {} section of config".format(name, kind))


class K8sClient:
    """Kubernetes API client."""

    VERSIONS = {
        "deployments": "apps/v1",
        "ingresses": "networking.k8s.io/v1",
        "pods": "v1",
        "replicasets": "apps/v1",
        "services": "v1",
        "jobs": "batch/v1",
        "cronjobs": "batch/v1",
        "limitranges": "v1",
        "resourcequotas": "v1",
        "configmaps": "v1",
        "events": "v1",
    }

    @classmethod
    def from_file(cls, filename=None):
        """Create a client from a kubeconfig file."""
        with open(filename, "r") as f:
            data = yaml.safe_load(f.read())

        context = _find_cfg_obj(data, "contexts", data["current-context"])
        cluster = _find_cfg_obj(data, "clusters", context["cluster"])
        user = _find_cfg_obj(data, "users", context["user"])

        return cls(
            server=cluster["server"],
            namespace=context["namespace"],
            tls_cert_file=user["client-certificate"],
            tls_key_file=user["client-key"],
            # assume this runs in a pod
            tls_ca_file="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
        )

    @classmethod
    def from_container_service_account(cls, *, namespace: str):
        """Create a client from the container default service account."""
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            token = f.read()

        return cls(
            server="https://kubernetes.default.svc",
            namespace=namespace,
            token=token,
            tls_ca_file="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
        )

    def __init__(
        self,
        *,
        server: str,
        namespace: str,
        token: Optional[str] = None,
        tls_cert_file: Optional[str] = None,
        tls_key_file: Optional[str] = None,
        tls_ca_file: str,
        timeout: int = 10,
    ):
        """Constructor."""
        self.timeout = timeout
        self.server = server
        self.namespace = namespace

        self.session = requests.Session()

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

        if tls_cert_file and tls_key_file:
            self.session.cert = (tls_cert_file, tls_key_file)

        self.session.verify = tls_ca_file
        self.session.headers[
            "User-Agent"
        ] = f"jobs-framework-api python-requests/{requests.__version__}"

    def _make_kwargs(self, url, **kwargs):
        """Setup kwargs for a Requests request."""
        version = kwargs.pop("version", "v1")
        if version == "v1":
            root = "api"
        else:
            root = "apis"
        kwargs["url"] = "{}/{}/{}/namespaces/{}/{}".format(
            self.server, root, version, self.namespace, url
        )
        name = kwargs.pop("name", None)
        if name is not None:
            kwargs["url"] = "{}/{}".format(kwargs["url"], name)
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return kwargs

    def _get(self, url, **kwargs):
        """GET request."""
        r = self.session.get(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.json()

    def _post(self, url, **kwargs):
        """POST request."""
        r = self.session.post(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.status_code

    def _delete(self, url, **kwargs):
        """DELETE request."""
        r = self.session.delete(**self._make_kwargs(url, **kwargs))
        r.raise_for_status()
        return r.status_code

    def get_object(self, kind, name):
        """Get the object with the specified name and of the given kind in the namespace."""
        return self._get(
            kind,
            name=name,
            version=K8sClient.VERSIONS[kind],
        )

    def get_objects(self, kind, selector=None, *, field_selector=None):
        """Get list of objects of the given kind in the namespace."""
        params = {}
        if selector:
            params["labelSelector"] = selector
        if field_selector:
            params["fieldSelector"] = field_selector

        return self._get(
            kind,
            params=params,
            version=K8sClient.VERSIONS[kind],
        )["items"]

    def delete_objects(self, kind, selector=None):
        """Delete objects of the given kind in the namespace."""
        if kind == "services":
            # Annoyingly Service does not have a Delete Collection option
            for svc in self.get_objects(kind, selector):
                self._delete(
                    kind,
                    name=svc["metadata"]["name"],
                    version=K8sClient.VERSIONS[kind],
                )
        else:
            deleteoptions = {
                "kind": "DeleteOptions",
                "apiVersion": "v1",
                "propagationPolicy": "Background",
            }

            self._delete(
                kind,
                params={"labelSelector": selector, "json": deleteoptions},
                version=K8sClient.VERSIONS[kind],
            )

    def create_object(self, kind, spec):
        """Create an object of the given kind in the namespace."""
        return self._post(
            kind,
            json=spec,
            version=K8sClient.VERSIONS[kind],
        )
