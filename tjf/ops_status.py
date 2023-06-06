# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2023 Arturo Borrero Gonzalez <aborrero@wikimedia.org>

from datetime import datetime
from typing import Optional
from tjf.error import TjfError
from tjf.labels import labels_selector
from tjf.job import Job
from tjf.user import User
from tjf.utils import KUBERNETES_DATE_FORMAT
import tjf.utils as utils


def _get_quota_error(message: str) -> str:
    keyword = "limited: "
    if keyword in message:
        quota_types = [
            utils.remove_prefixes(entry.split("=")[0], ("requests.", "limits."))
            for entry in message[message.rindex(keyword) + len(keyword) :].split(",")
        ]
    else:
        quota_types = []

    return f"out of quota for {', '.join(sorted(quota_types))}"


def _get_job_object_status(user: User, job: dict, for_complete=False) -> Optional[str]:
    if not job:
        return None

    status_dict = utils.dict_get_object(job, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Complete" and for_complete:
            if condition["status"] == "True":
                return "Completed"
            elif condition["status"] == "False":
                return "Not running"

    if status_dict.get("failed", None) is not None:
        return "Failed"

    if (
        status_dict.get("active", None) is not None
        and status_dict.get("startTime", None) is not None
    ):
        start_time = datetime.strptime(status_dict["startTime"], KUBERNETES_DATE_FORMAT)
        running_for = int((datetime.now() - start_time).total_seconds())
        return f"Running for {utils.format_duration(running_for)}"

    job_uid = job["metadata"]["uid"]
    events = user.kapi.get_objects("events", field_selector=f"involvedObject.uid={job_uid}")
    for event in sorted(events, key=lambda event: event["lastTimestamp"], reverse=True):
        reason = event.get("reason", None)

        if reason == "FailedCreate":
            message = "Unable to start"

            event_message = event.get("message", None)
            if event_message and "is forbidden: exceeded quota" in event_message:
                message += f", {_get_quota_error(event_message)}"

            return message


def _refresh_status_cronjob_from_restarted_cronjob(
    user: User, original_cronjob: Job
) -> Optional[str]:
    """This function scans all job resources that may or may not be manually defined to see if
    it may be related to the original_cronjob."""
    original_cronjob_metadata = original_cronjob.k8s_object.get("metadata", None)
    if not original_cronjob_metadata:
        return None

    original_cronjob_uid = original_cronjob_metadata.get("uid", None)
    if not original_cronjob_uid:
        return None

    label_selector = labels_selector(
        jobname=original_cronjob.jobname, username=user.name, type="cronjobs"
    )
    all_cronjob_jobs = user.kapi.get_objects("jobs", label_selector=label_selector)
    for maybe_manual_job_data in all_cronjob_jobs:
        metadata = maybe_manual_job_data.get("metadata", None)
        if not metadata:
            # can't do anything without it, ignore this job
            continue

        annotations = metadata.get("annotations", None)
        if not annotations:
            continue

        instantiate = annotations.get("cronjob.kubernetes.io/instantiate", None)
        if instantiate != "manual":
            continue

        ownerreferences = metadata.get("ownerReferences", None)
        if not ownerreferences:
            continue

        matching_reference = False
        for reference in ownerreferences:
            if reference.get("kind", None) != "CronJob":
                continue

            if reference.get("name", None) != original_cronjob.jobname:
                continue

            if reference.get("uid", None) == original_cronjob_uid:
                matching_reference = True

        if not matching_reference:
            continue

        maybe_job = Job.from_k8s_object(maybe_manual_job_data, "jobs")
        if maybe_job.command != original_cronjob.command:
            continue

        # finally, everything matches, we are certain this job was manually created from the cronjob
        job_status = _get_job_object_status(user, maybe_manual_job_data)
        if job_status:
            return job_status


def _refresh_status_cronjob(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")

    last = status_dict.get("lastScheduleTime", None)
    if last:
        job.status_short = f"Last schedule time: {last}"
    else:
        job.status_short = "Waiting for scheduled time"

    for active_job in status_dict.get("active", []):
        job_data = user.kapi.get_object("jobs", active_job["name"])
        if not job_data:
            continue

        job_status = _get_job_object_status(user, job_data)
        if job_status:
            job.status_short = job_status
            # we found something! that's enough
            return

    # if we didn't find anything yet, try searching for manually restarted cronjobs
    job_status = _refresh_status_cronjob_from_restarted_cronjob(user, original_cronjob=job)
    if job_status:
        job.status_short = job_status


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
            quota_error = _get_quota_error(condition["message"])
            job.status_short = f"Unable to start, {quota_error}"

    # Attempt to gather more details if possible
    if job.status_short == "Not running":
        pod_selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
        pods = user.kapi.get_objects("pods", label_selector=pod_selector)

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
    job_status = _get_job_object_status(user, job.k8s_object, for_complete=True)
    if job_status:
        job.status_short = job_status
    else:
        job.status_short = "Unknown"


def refresh_job_short_status(user: User, job: Job):
    if job.k8s_type == "cronjobs":
        _refresh_status_cronjob(user, job)
    elif job.k8s_type == "deployments":
        _refresh_status_dp(user, job)
    elif job.k8s_type == "jobs":
        _refresh_status_job(user, job)
    else:
        raise TjfError(f"Unable to refresh status for unknown job type: {job}")


def refresh_job_long_status(user: User, job: Job):
    label_selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
    podlist = user.kapi.get_objects("pods", label_selector=label_selector)

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
