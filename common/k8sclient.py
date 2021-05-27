# from tools-webservice toolsws/backends/kubernetes.py
# copyright TBD

import os
import subprocess
import requests
import urllib3
import yaml

class KubectlClient():
    def kubectl(args, content):
        cmd = "kubectl {}".format(args)
        if content:
            file = "kubectl_data_file.yaml"
            if os.path.exists(file):
                os.remove(file)
            with open(file, "w") as filehandler:
                yaml.dump(content, filehandler)
            cmd = cmd + " -f {}".format(file)

        print(cmd)
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        if r.returncode != 0:
            print("E: command failed {}".format(cmd))

        if r.stdout:
            return r.stdout.decode("utf-8")

# T253412: Disable warnings about unverifed TLS certs when talking to the
# Kubernetes API endpoint
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class K8sClient(object):
    """Kubernetes API client."""

    VERSIONS = {
        "deployments": "apps/v1",
        "ingresses": "networking.k8s.io/v1beta1",
        "pods": "v1",
        "replicasets": "apps/v1",
        "services": "v1",
        "jobs": "batch/v1",
        "cronjobs": "batch/v1beta1",
        "replicationcontrollers": "v1",
    }

    @classmethod
    def from_file(cls, filename=None):
        """Create a client from a kubeconfig file."""
        if not filename:
            filename = os.getenv("KUBECONFIG", "~/.kube/config")
        filename = os.path.expanduser(filename)
        with open(filename) as f:
            data = yaml.safe_load(f.read())
        return cls(data)

    def __init__(self, config, timeout=10):
        """Constructor."""
        self.config = config
        self.timeout = timeout
        self.context = self._find_cfg_obj(
            "contexts", config["current-context"]
        )
        self.cluster = self._find_cfg_obj("clusters", self.context["cluster"])
        self.server = self.cluster["server"]
        self.namespace = self.context["namespace"]

        user = self._find_cfg_obj("users", self.context["user"])
        self.session = requests.Session()
        self.session.cert = (user["client-certificate"], user["client-key"])
        # T253412: We are deliberately not validating the api endpoint's TLS
        # certificate. The only way to do this with a self-signed cert is to
        # pass the path to a CA bundle. We actually *can* do that, but with
        # python2 we have seen the associated clean up code fail and leave
        # /tmp full of orphan files.
        self.session.verify = False

    def _find_cfg_obj(self, kind, name):
        """Lookup a named object in our config."""
        for obj in self.config[kind]:
            if obj["name"] == name:
                return obj[kind[:-1]]
        raise KeyError(
            "Key {} not found in {} section of config".format(name, kind)
        )

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

    def get_objects(self, kind, selector=None):
        """Get list of objects of the given kind in the namespace."""
        return self._get(
            kind,
            params={"labelSelector": selector},
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
            self._delete(
                kind,
                params={"labelSelector": selector},
                version=K8sClient.VERSIONS[kind],
            )

    def create_object(self, kind, spec):
        """Create an object of the given kind in the namespace."""
        return self._post(
            kind,
            json=spec,
            version=K8sClient.VERSIONS[kind],
        )
