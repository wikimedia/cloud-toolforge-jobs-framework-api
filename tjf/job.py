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
import time
from tjf.error import TjfError, TjfValidationError
from tjf.images import Image, image_by_container_url
import tjf.utils as utils
from common.k8sclient import K8sClient
from tjf.labels import generate_labels
from tjf.command import Command

# This is a restriction by Kubernetes:
# a lowercase RFC 1123 subdomain must consist of lower case alphanumeric
# characters, '-' or '.', and must start and end with an alphanumeric character
JOBNAME_PATTERN = re.compile("^[a-z0-9]([-a-z0-9]*[a-z0-9])?([.][a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")


def validate_jobname(jobname: str):
    if jobname is None:
        # nothing to validate
        return

    if not JOBNAME_PATTERN.match(jobname):
        raise TjfValidationError(
            "Invalid job name. See the documentation for the naming rules: https://w.wiki/6YL8"
        )


def validate_emails(emails: str):
    if emails is None:
        # nothing to validate
        return

    values = ["none", "all", "onfailure", "onfinish"]
    if emails not in values:
        raise TjfValidationError(
            f"Invalid email configuration value. Supported values are: {values}"
        )


JOB_DEFAULT_MEMORY = "512Mi"
JOB_DEFAULT_CPU = "500m"
# tell kubernetes to delete jobs this many seconds after they finish
JOB_TTLAFTERFINISHED = 30


class Job:
    def __init__(
        self,
        command: Command,
        image: Image,
        jobname,
        ns,
        username,
        schedule,
        cont,
        k8s_object,
        retry: int,
        memory: str,
        cpu: str,
        emails: str,
    ):
        self.command = command
        self.image = image
        self.jobname = jobname
        self.ns = ns
        self.username = username
        self.status_short = "Unknown"
        self.status_long = "Unknown"
        self.schedule = schedule
        self.cont = cont
        self.k8s_object = k8s_object
        self.memory = memory
        self.cpu = cpu
        self.emails = emails
        self.retry = retry

        if self.emails is None:
            self.emails = "none"

        if self.schedule is not None:
            self.k8s_type = "cronjobs"
        elif self.cont is True:
            self.k8s_type = "deployments"
        else:
            self.k8s_type = "jobs"

        validate_jobname(self.jobname)
        validate_emails(self.emails)
        utils.validate_kube_quant(self.memory)
        utils.validate_kube_quant(self.cpu)

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
            raise TjfError("Unable to parse Kubernetes object", data={"object": object})

        metadata = utils.dict_get_object(object, "metadata")
        jobname = metadata["name"]
        namespace = metadata["namespace"]
        user = "".join(namespace.split("-", 1)[1:])
        image = podspec["template"]["spec"]["containers"][0]["image"]
        retry = podspec.get("backoffLimit", 0)
        emails = metadata["labels"].get("jobs.toolforge.org/emails", "none")
        resources = podspec["template"]["spec"]["containers"][0].get("resources", {})
        resources_limits = resources.get("limits", {})
        memory = resources_limits.get("memory", JOB_DEFAULT_MEMORY)
        cpu = resources_limits.get("cpu", JOB_DEFAULT_CPU)

        k8s_command = podspec["template"]["spec"]["containers"][0]["command"]
        k8s_arguments = podspec["template"]["spec"]["containers"][0].get("arguments", None)
        command = Command.from_k8s(
            k8s_metadata=metadata, k8s_command=k8s_command, k8s_arguments=k8s_arguments
        )

        return cls(
            command=command,
            image=image_by_container_url(image),
            jobname=jobname,
            ns=namespace,
            username=user,
            schedule=schedule,
            cont=cont,
            k8s_object=object,
            retry=retry,
            memory=memory,
            cpu=cpu,
            emails=emails,
        )

    def _generate_container_resources(self):
        # this function was adapted from toollabs-webservice toolsws/backends/kubernetes.py
        container_resources = {}

        if self.memory or self.cpu:
            container_resources = {"limits": {}, "requests": {}}

        if self.memory:
            dec_mem = utils.parse_quantity(self.memory)
            if dec_mem < utils.parse_quantity(JOB_DEFAULT_MEMORY):
                container_resources["requests"]["memory"] = self.memory
            else:
                container_resources["requests"]["memory"] = str(dec_mem / 2)
            container_resources["limits"]["memory"] = self.memory

        if self.cpu:
            dec_cpu = utils.parse_quantity(self.cpu)
            if dec_cpu < utils.parse_quantity(JOB_DEFAULT_CPU):
                container_resources["requests"]["cpu"] = self.cpu
            else:
                container_resources["requests"]["cpu"] = str(dec_cpu / 2)
            container_resources["limits"]["cpu"] = self.cpu

        return container_resources

    def _get_k8s_podtemplate(self, restartpolicy):
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.command.filelog,
            emails=self.emails,
        )
        generated_command = self.command.generate_for_k8s()

        if self.image.type.use_standard_nfs():
            working_dir = f"/data/project/{self.username}"
            env = []
        else:
            working_dir = None
            env = [
                {
                    "name": "NO_HOME",
                    "value": "a buildservice pod does not need a home env",
                }
            ]

        return {
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "restartPolicy": restartpolicy,
                    "containers": [
                        {
                            "name": "job",
                            "image": self.image.container,
                            "workingDir": working_dir,
                            "env": env,
                            "command": generated_command.command,
                            "args": generated_command.args,
                            "resources": self._generate_container_resources(),
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
            filelog=self.command.filelog,
            emails=self.emails,
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
                "startingDeadlineSeconds": 30,
                "jobTemplate": {"spec": self._get_k8s_podtemplate(restartpolicy="Never")},
            },
        }

        obj["spec"]["jobTemplate"]["spec"]["ttlSecondsAfterFinished"] = JOB_TTLAFTERFINISHED
        obj["spec"]["jobTemplate"]["spec"]["backoffLimit"] = self.retry

        return obj

    def _get_k8s_deployment_object(self):
        labels = generate_labels(
            jobname=self.jobname,
            username=self.username,
            type=self.k8s_type,
            filelog=self.command.filelog,
            emails=self.emails,
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
            filelog=self.command.filelog,
            emails=self.emails,
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
        obj["spec"]["ttlSecondsAfterFinished"] = JOB_TTLAFTERFINISHED
        obj["spec"]["backoffLimit"] = self.retry

        return obj

    def get_k8s_object(self):
        if self.k8s_type == "cronjobs":
            return self._get_k8s_cronjob_object()

        if self.k8s_type == "deployments":
            return self._get_k8s_deployment_object()

        return self._get_k8s_job_object()

    def get_k8s_single_run_object(self, cronjob_uid):
        """Returns a Kubernetes manifest to run this CronJob once."""
        # This is largely based on kubectl code
        # https://github.com/kubernetes/kubernetes/blob/985c9202ccd250a5fe22c01faf0d8f83d804b9f3/staging/src/k8s.io/kubectl/pkg/cmd/create/create_job.go#L261

        k8s_job_object = self._get_k8s_job_object()

        # Set an unique name
        k8s_job_object["metadata"]["name"] += f"-{int(time.time())}"

        # Set references to the CronJob object
        k8s_job_object["metadata"]["annotations"] = {"cronjob.kubernetes.io/instantiate": "manual"}
        k8s_job_object["metadata"]["ownerReferences"] = [
            {
                "apiVersion": K8sClient.VERSIONS["cronjobs"],
                "kind": "CronJob",
                "name": self.jobname,
                "uid": cronjob_uid,
            }
        ]

        return k8s_job_object

    def get_api_object(self):
        obj = {
            "name": self.jobname,
            "cmd": self.command.user_command,
            "image": self.image.canonical_name,
            "image_state": self.image.state,
            "filelog": f"{self.command.filelog}",
            "filelog_stdout": self.command.filelog_stdout,
            "filelog_stderr": self.command.filelog_stderr,
            "status_short": self.status_short,
            "status_long": self.status_long,
            "emails": self.emails,
            "retry": self.retry,
        }

        if self.schedule is not None:
            obj["schedule"] = self.schedule

        if self.cont:
            obj["continuous"] = True

        if self.memory is not None and self.memory != JOB_DEFAULT_MEMORY:
            obj["memory"] = self.memory

        if self.cpu is not None and self.cpu != JOB_DEFAULT_CPU:
            obj["cpu"] = self.cpu

        return obj
