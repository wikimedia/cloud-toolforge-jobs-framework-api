from tjf.containers import container_get_shortname
from tjf.user import User
import tjf.utils as utils
from common.k8sclient import K8sClient


def delete_job(user: User, jobname: str):
    for object in ["jobs", "cronjobs", "deployments", "pods"]:
        user.kapi.delete_objects(object, selector=Job.get_labels_selector(jobname, user.name))


def find_job(user: User, jobname: str):
    list = list_all_jobs(user=user, jobname=jobname)

    for job in list:
        if job.jobname == jobname:
            return job


def list_all_jobs(user: User, jobname: str):
    selector = Job.get_labels_selector(jobname=jobname, username=user.name)

    job_list = []
    for kind in ["jobs", "cronjobs", "deployments"]:
        for job in user.kapi.get_objects(kind, selector=selector):
            job_list.append(Job.from_k8s_object(object=job, kind=kind))

    return job_list


class Job:
    def __init__(self, cmd, image, jobname, ns, username, status, schedule, cont):
        self.cmd = cmd
        self.image = image
        self.jobname = jobname
        self.ns = ns
        self.username = username
        if not status:
            status = "unknown"
        self.status = status
        self.schedule = schedule
        self.cont = cont

        if self.schedule is not None:
            self.k8s_type = "cronjobs"
        elif self.cont is True:
            self.k8s_type = "deployments"
        else:
            self.k8s_type = "jobs"

    @classmethod
    def get_labels(self, jobname, username):
        obj = {
            "toolforge": "tool",
            "app.kubernetes.io/component": "tool",
            "app.kubernetes.io/version": "1",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/created-by": username,
        }

        if jobname is not None:
            obj["app.kubernetes.io/name"] = jobname

        return obj

    @classmethod
    def get_labels_selector(self, jobname, username):
        return ",".join(
            ["{k}={v}".format(k=k, v=v) for k, v in self.get_labels(jobname, username).items()]
        )

    def _parse_k8s_podtemplate(self, object, podspec, schedule, cont):
        metadata = utils.dict_get_object(object, "metadata")
        jobname = metadata["name"]
        namespace = metadata["namespace"]
        user = "".join(namespace.split("-")[1:])

        cmd = podspec["template"]["spec"]["containers"][0]["command"][0]
        image = podspec["template"]["spec"]["containers"][0]["image"]

        status = "unknown"
        status_dict = utils.dict_get_object(object, "status")
        if status_dict and status_dict.get("conditions", None):
            for condition in status_dict["conditions"]:
                if condition["type"] == "Failed":
                    status = "failed"

        return Job(cmd, image, jobname, namespace, user, status, schedule=schedule, cont=cont)

    @classmethod
    def from_k8s_object(self, object: dict, kind: str):
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

        return self._parse_k8s_podtemplate(
            self, object=object, podspec=podspec, schedule=schedule, cont=cont
        )

    def _get_k8s_podtemplate(self, restartpolicy):
        return {
            "template": {
                "metadata": {"labels": self.get_labels(self.jobname, self.username)},
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
        return {
            "apiVersion": K8sClient.VERSIONS["cronjobs"],
            "kind": "CronJob",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": self.get_labels(self.jobname, self.username),
            },
            "spec": {
                "schedule": self.schedule,
                "jobTemplate": {"spec": self._get_k8s_podtemplate(restartpolicy="Never")},
            },
        }

    def _get_k8s_deployment_object(self):
        obj = {
            "kind": "Deployment",
            "apiVersion": K8sClient.VERSIONS["deployments"],
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": self.get_labels(self.jobname, self.username),
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Always"),
        }

        obj["spec"]["replicas"] = 1
        obj["spec"]["selector"] = {
            "matchLabels": self.get_labels(self.jobname, self.username),
        }

        return obj

    def _get_k8s_job_object(self):
        obj = {
            "apiVersion": K8sClient.VERSIONS["jobs"],
            "kind": "Job",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": self.get_labels(self.jobname, self.username),
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Never"),
        }

        # delete job when it finishes. This somewhat mimics grid behavior, no?
        obj["spec"]["ttlSecondsAfterFinished"] = 0

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
