import tjf.utils as utils


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
        return {
            "toolforge": "tool",
            "app.kubernetes.io/component": "tool",
            "app.kubernetes.io/version": "1",
            "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
            "app.kubernetes.io/name": jobname,
            "app.kubernetes.io/created-by": username,
        }

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
    def from_cronjob_k8s_object(self, cronjob_definition):
        spec = utils.dict_get_object(cronjob_definition, "spec")
        schedule = spec["schedule"]

        return self._parse_k8s_podtemplate(
            self,
            object=cronjob_definition,
            podspec=spec["jobTemplate"]["spec"],
            schedule=schedule,
            cont=False,
        )

    @classmethod
    def from_dp_k8s_object(self, deployment_definition):
        podspec = utils.dict_get_object(deployment_definition, "spec")

        return self._parse_k8s_podtemplate(
            self, object=deployment_definition, podspec=podspec, schedule=None, cont=True
        )

    @classmethod
    def from_job_k8s_object(self, job_definition):
        podspec = utils.dict_get_object(job_definition, "spec")

        return self._parse_k8s_podtemplate(
            self, object=job_definition, podspec=podspec, schedule=None, cont=False
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
            "apiVersion": "batch/v1",
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
            "apiVersion": "apps/v1",
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
        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": self.get_labels(self.jobname, self.username),
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Never"),
        }

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
            "image": self.image,
            "user": self.username,
            "namespace": self.ns,
            "status": self.status,
        }

        if self.schedule is not None:
            obj["schedule"] = self.schedule

        if self.cont:
            obj["continuous"] = True

        return obj
