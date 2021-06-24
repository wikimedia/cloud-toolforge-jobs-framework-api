from tjf.containers import container_get_shortname
import tjf.utils as utils
from common.k8sclient import K8sClient
from tjf.labels import labels


class Job:
    def __init__(self, cmd, image, jobname, ns, username, schedule, cont, k8s_object):
        self.cmd = cmd
        self.image = image
        self.jobname = jobname
        self.ns = ns
        self.username = username
        self.status_short = "Unknown"
        self.status_long = "Unknown"
        self.schedule = schedule
        self.cont = cont
        self.k8s_object = k8s_object

        if self.schedule is not None:
            self.k8s_type = "cronjobs"
        elif self.cont is True:
            self.k8s_type = "deployments"
        else:
            self.k8s_type = "jobs"

    @classmethod
    def from_k8s_object(cls, object: dict, kind: str):
        spec = utils.dict_get_object(object, "spec")

        if kind == "cronjobs":
            schedule = spec["schedule"]
            cont = False
            podspec = spec["jobTemplate"]["spec"]
        elif kind == "deployments":
            schedule = None
            cont = True
            podspec = spec
        elif kind == "jobs":
            schedule = None
            cont = False
            podspec = spec
        else:
            raise Exception(f"received a kubernetes object we don't understand: {object}")

        metadata = utils.dict_get_object(object, "metadata")
        jobname = metadata["name"]
        namespace = metadata["namespace"]
        user = "".join(namespace.split("-")[1:])

        cmd = podspec["template"]["spec"]["containers"][0]["command"][0]
        image = podspec["template"]["spec"]["containers"][0]["image"]

        return cls(
            cmd=cmd,
            image=image,
            jobname=jobname,
            ns=namespace,
            username=user,
            schedule=schedule,
            cont=cont,
            k8s_object=object,
        )

    def _get_k8s_podtemplate(self, restartpolicy):
        return {
            "template": {
                "metadata": {"labels": labels(self.jobname, self.username, self.k8s_type)},
                "spec": {
                    "restartPolicy": restartpolicy,
                    "containers": [
                        {
                            "name": self.jobname,
                            "image": self.image,
                            "workingDir": "/data/project/{}".format(self.username),
                            "command": [self.cmd],
                            "env": [
                                {"name": "HOME", "value": "/data/project/{}".format(self.username)}
                            ],
                            "volumeMounts": [{"mountPath": "/data/project", "name": "home"}],
                        }
                    ],
                    "volumes": [
                        {
                            "name": "home",
                            "hostPath": {"path": "/data/project", "type": "Directory"},
                        }
                    ],
                },
            }
        }

    def _get_k8s_cronjob_object(self):
        obj = {
            "apiVersion": K8sClient.VERSIONS["cronjobs"],
            "kind": "CronJob",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels(self.jobname, self.username, self.k8s_type),
            },
            "spec": {
                "schedule": self.schedule,
                "successfulJobsHistoryLimit": 0,
                "failedJobsHistoryLimit": 0,
                "concurrencyPolicy": "Forbid",
                "jobTemplate": {"spec": self._get_k8s_podtemplate(restartpolicy="Never")},
            },
        }

        obj["spec"]["jobTemplate"]["spec"]["ttlSecondsAfterFinished"] = 0
        obj["spec"]["jobTemplate"]["spec"]["backoffLimit"] = 1

        return obj

    def _get_k8s_deployment_object(self):
        obj = {
            "kind": "Deployment",
            "apiVersion": K8sClient.VERSIONS["deployments"],
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels(self.jobname, self.username, self.k8s_type),
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Always"),
        }

        obj["spec"]["replicas"] = 1
        obj["spec"]["selector"] = {
            "matchLabels": labels(self.jobname, self.username, self.k8s_type),
        }

        return obj

    def _get_k8s_job_object(self):
        obj = {
            "apiVersion": K8sClient.VERSIONS["jobs"],
            "kind": "Job",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels(self.jobname, self.username, self.k8s_type),
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Never"),
        }

        # delete job when it finishes. This somewhat mimics grid behavior, no?
        obj["spec"]["ttlSecondsAfterFinished"] = 0
        obj["spec"]["backoffLimit"] = 1

        return obj

    def get_k8s_object(self):
        if self.k8s_type == "cronjobs":
            return self._get_k8s_cronjob_object()

        if self.k8s_type == "deployments":
            return self._get_k8s_deployment_object()

        return self._get_k8s_job_object()

    def get_api_object(self):
        obj = {
            "name": self.jobname,
            "cmd": self.cmd,
            "image": container_get_shortname(self.image),
            "user": self.username,
            "namespace": self.ns,
            "status_short": self.status_short,
            "status_long": self.status_long,
        }

        if self.schedule is not None:
            obj["schedule"] = self.schedule

        if self.cont:
            obj["continuous"] = True

        return obj
