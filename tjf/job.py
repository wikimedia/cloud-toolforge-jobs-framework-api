import tjf.utils as utils


class Job:
    def __init__(self, cmd, image, jobname, ns, username, status):
        self.cmd = cmd
        self.image = image
        self.jobname = jobname
        self.ns = ns
        self.username = username
        if not status:
            status = "unknown"
        self.status = status

    @classmethod
    def from_k8s_object(self, job_definition):
        metadata = utils.dict_get_object(job_definition, "metadata")
        jobname = metadata["name"]
        namespace = metadata["namespace"]
        user = "".join(namespace.split("-")[1:])

        spec = utils.dict_get_object(job_definition, "spec")
        cmd = spec["template"]["spec"]["containers"][0]["command"][0]
        image = spec["template"]["spec"]["containers"][0]["image"]

        status = "unknown"
        status_dict = utils.dict_get_object(job_definition, "status")
        if status_dict and status_dict.get("conditions", None):
            for condition in status_dict["conditions"]:
                if condition["type"] == "Failed":
                    status = "failed"

        return Job(cmd, image, jobname, namespace, user, status)

    def get_k8s_object(self):
        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
            },
            "spec": {
                "backoffLimit": 3,
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [
                            {
                                "name": self.jobname,
                                "image": self.image,
                                "workingDir": "/data/project/{}".format(self.username),
                                "command": [
                                    self.cmd,
                                ],
                                "env": [
                                    {
                                        "name": "HOME",
                                        "value": "/data/project/{}".format(self.username),
                                    },
                                ],
                                "volumeMounts": [
                                    {
                                        "mountPath": "/data/project",
                                        "name": "home",
                                    },
                                ],
                            },
                        ],
                        "volumes": [
                            {
                                "name": "home",
                                "hostPath": {
                                    "path": "/data/project",
                                    "type": "Directory",
                                },
                            }
                        ],
                    },
                },
            },
        }

    def get_api_object(self):
        return {
            "name": self.jobname,
            "cmd": self.cmd,
            "image": self.image,
            "user": self.username,
            "namespace": self.ns,
            "status": self.status,
        }
