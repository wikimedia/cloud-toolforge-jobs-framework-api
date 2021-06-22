from tjf.containers import container_get_shortname
from tjf.user import User
import tjf.utils as utils
from common.k8sclient import K8sClient


def delete_job(user: User, jobname: str):
    for object in ["jobs", "cronjobs", "deployments"]:
        user.kapi.delete_objects(object, selector=labels_selector(jobname, user.name, object))

    # extra explicit cleanup of jobs (may have been created by cronjobs)
    user.kapi.delete_objects("jobs", selector=labels_selector(jobname, user.name, None))

    # extra explicit cleanup of pods
    user.kapi.delete_objects("pods", selector=labels_selector(jobname, user.name, None))


def find_job(user: User, jobname: str):
    list = list_all_jobs(user=user, jobname=jobname)

    for job in list:
        if job.jobname == jobname:
            return job


def list_all_jobs(user: User, jobname: str):
    job_list = []

    for kind in ["jobs", "cronjobs", "deployments"]:
        selector = labels_selector(jobname=jobname, username=user.name, type=kind)
        for job in user.kapi.get_objects(kind, selector=selector):
            job_list.append(Job.from_k8s_object(object=job, kind=kind))

    return job_list


def labels(jobname: str, username: str, type: str):
    obj = {
        "toolforge": "tool",
        "app.kubernetes.io/version": "1",
        "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
        "app.kubernetes.io/created-by": username,
    }

    if type is not None:
        obj["app.kubernetes.io/component"] = type

    if jobname is not None:
        obj["app.kubernetes.io/name"] = jobname

    return obj


def labels_selector(jobname: str, username: str, type: str):
    return ",".join(
        ["{k}={v}".format(k=k, v=v) for k, v in labels(jobname, username, type).items()]
    )


class Job:
    def __init__(self, cmd, image, jobname, ns, username, schedule, cont, k8s_object):
        self.cmd = cmd
        self.image = image
        self.jobname = jobname
        self.ns = ns
        self.username = username
        self.status = "unknown"
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
            "status": self.status,
        }

        if self.schedule is not None:
            obj["schedule"] = self.schedule

        if self.cont:
            obj["continuous"] = True

        return obj
