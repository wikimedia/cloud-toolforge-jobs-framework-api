# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023 Arturo Borrero Gonzalez <aborrero@wikimedia.org>

from tjf.labels import labels_selector
from tjf.job import Job
from tjf.user import User
import tjf.utils as utils


def _refresh_status_cronjob(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    last = status_dict.get("lastScheduleTime", "unknown")
    job.status_short = f"Last schedule time: {last}"


def _refresh_status_dp(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Available":
            if condition["status"] == "True":
                job.status_short = "Running"
            elif condition["status"] == "False":
                job.status_short = "Not running"
        elif (
            condition["type"] == "ReplicaFailure"
            and condition["reason"] == "FailedCreate"
            and condition["status"] == "True"
            and "forbidden: exceeded quota" in condition["message"]
        ):
            job.status_short = "Unable to start, out of quota"

    # Attempt to gather more details if possible
    if job.status_short == "Not running":
        pod_selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
        pods = user.kapi.get_objects("pods", selector=pod_selector)

        for pod in pods:
            if "containerStatuses" not in pod["status"]:
                continue

            for container_status in pod["status"]["containerStatuses"]:
                if "state" not in container_status:
                    continue

                if (
                    "waiting" in container_status["state"]
                    and container_status["state"]["waiting"]["reason"] == "CrashLoopBackOff"
                ) or (
                    "terminated" in container_status["state"]
                    and container_status["state"]["terminated"]["reason"] == "Error"
                ):
                    job.status_short = "Fails to start"


def _refresh_status_job(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Complete":
            if condition["status"] == "True":
                job.status_short = "Completed"
                return
            elif condition["status"] == "False":
                job.status_short = "Not running"
                return

    if status_dict.get("failed", None) is not None:
        job.status_short = "Failed"
        return

    if status_dict.get("active", None) is not None:
        job.status_short = "Running"
        return


def refresh_job_short_status(user: User, job: Job):
    if job.k8s_type == "cronjobs":
        _refresh_status_cronjob(user, job)
    elif job.k8s_type == "deployments":
        _refresh_status_dp(user, job)
    elif job.k8s_type == "jobs":
        _refresh_status_job(user, job)
    else:
        raise Exception(f"couldn't refresh status for unknown job type: {job}")


def refresh_job_long_status(user: User, job: Job):
    selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
    podlist = user.kapi.get_objects("pods", selector=selector)

    if len(podlist) == 0:
        job.status_long = "No pods were created for this job."
        return

    # we only evaluate the first pod, we should be creating 1 pod per job anyway
    pod = podlist[0]

    starttime = pod["status"].get("startTime", None)
    if starttime is not None:
        job.status_long = f"Last run at {starttime}."
    else:
        job.status_long = "Run not attempted yet."

    # https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase
    phase = pod["status"].get("phase", "unknown")
    job.status_long += f" Pod in '{phase}' phase."

    statuses = pod["status"].get("containerStatuses", [])
    if len(statuses) == 0:
        # nothing else to report
        return

    # we only have 1 container per pod
    containerstatus = statuses[0]

    restartcount = containerstatus["restartCount"]
    if restartcount > 0:
        job.status_long += f" Pod has been restarted {restartcount} times."

    # the pod didn't have a lastState, is currently live! (failing or not)
    currentstate = containerstatus["state"]

    # please python, I just need the key as a string
    for c in currentstate:
        state = c
        break

    job.status_long += f" State '{state}'."

    reason = containerstatus["state"][state].get("reason", "unknown")
    if state != "running" or reason != "unknown":
        job.status_long += f" Reason '{reason}'."

    start = containerstatus["state"][state].get("startedAt", "unknown")
    if start != "unknown":
        job.status_long += f" Started at '{start}'."

    finish = containerstatus["state"][state].get("finishedAt", "unknown")
    if finish != "unknown":
        job.status_long += f" Finished at '{finish}'."

    rc = containerstatus["state"][state].get("exitCode", "unknown")
    if rc != "unknown":
        job.status_long += f" Exit code '{rc}'."

    msg = containerstatus["state"][state].get("message", "")
    if msg != "":
        job.status_long += f" Additional message:'{msg}'."
