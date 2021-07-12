# Copyright (C) 2021 Arturo Borrero Gonzalez <aborrero@wikimedia.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import re
from tjf.containers import container_get_shortname
import tjf.utils as utils
from common.k8sclient import K8sClient
from tjf.labels import generate_labels

JOBNAME_PATTERN = re.compile("^[a-zA-Z0-9-]{1,100}$")


def validate_jobname(jobname: str):
    if jobname is None:
        # nothing to validate
        return

    if not JOBNAME_PATTERN.match(jobname):
        # TODO: this could be a more 'custom' exception
        raise Exception(f"job name doesn't match regex {JOBNAME_PATTERN.pattern}")


def _filelog_string(jobname: str, filelog: bool):
    if filelog:
        return f" 1>{jobname}.out 2>{jobname}.err"

    return " 1>/dev/null 2>/dev/null"


# NOTE: this means the container needs /bin/sh :-S A future person needs to validate/enforce that
JOB_CMD_WRAPPER = ["/bin/sh", "-c", "--"]


class Job:
    def __init__(
        self, cmd, image, jobname, ns, username, schedule, cont, k8s_object, filelog: bool
    ):
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
        self.filelog = filelog

        if self.schedule is not None:
            self.k8s_type = "cronjobs"
        elif self.cont is True:
            self.k8s_type = "deployments"
        else:
            self.k8s_type = "jobs"

        validate_jobname(self.jobname)

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
        image = podspec["template"]["spec"]["containers"][0]["image"]

        _filelog = metadata["labels"].get("jobs.toolforge.org/filelog", "no")
        if _filelog == "yes":
            filelog = True
        else:
            filelog = False

        # the user specified command should be the last element in the cmd array
        _cmd = podspec["template"]["spec"]["containers"][0]["command"][-1]
        # remove log substring, which should be the last thing in the command string
        cmd = _cmd[: -len(_filelog_string(jobname, filelog))]

        return cls(
            cmd=cmd,
            image=image,
            jobname=jobname,
            ns=namespace,
            username=user,
            schedule=schedule,
            cont=cont,
            k8s_object=object,
            filelog=filelog,
        )

    def _generate_job_command(self):
        k8s_cmd_array = JOB_CMD_WRAPPER.copy()
        # separation space is returned by  _filelog_string()
        k8s_cmd_array.append(f"{self.cmd}{_filelog_string(self.jobname, self.filelog)}")

        return k8s_cmd_array

    def _get_k8s_podtemplate(self, restartpolicy):
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.filelog,
        )
        return {
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "restartPolicy": restartpolicy,
                    "containers": [
                        {
                            "name": self.jobname,
                            "image": self.image,
                            "workingDir": "/data/project/{}".format(self.username),
                            "command": self._generate_job_command(),
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
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.filelog,
        )
        obj = {
            "apiVersion": K8sClient.VERSIONS["cronjobs"],
            "kind": "CronJob",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels,
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
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.filelog,
        )
        obj = {
            "kind": "Deployment",
            "apiVersion": K8sClient.VERSIONS["deployments"],
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels,
            },
            "spec": self._get_k8s_podtemplate(restartpolicy="Always"),
        }

        obj["spec"]["replicas"] = 1
        obj["spec"]["selector"] = {
            "matchLabels": labels,
        }

        return obj

    def _get_k8s_job_object(self):
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.filelog,
        )
        obj = {
            "apiVersion": K8sClient.VERSIONS["jobs"],
            "kind": "Job",
            "metadata": {
                "name": self.jobname,
                "namespace": self.ns,
                "labels": labels,
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
            "filelog": f"{self.filelog}",
            "status_short": self.status_short,
            "status_long": self.status_long,
        }

        if self.schedule is not None:
            obj["schedule"] = self.schedule

        if self.cont:
            obj["continuous"] = True

        return obj
