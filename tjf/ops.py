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

import time
from tjf.labels import labels_selector
from tjf.job import Job, validate_jobname
from tjf.user import User
import tjf.utils as utils
from tjf.ops_status import refresh_job_short_status, refresh_job_long_status


def validate_job_limits(user: User, job: Job):
    limits = user.kapi.get_object("limitranges", name=user.namespace)["spec"]["limits"]

    for limit in limits:
        if limit["type"] != "Container":
            continue

        max_limits = limit["max"]
        if "cpu" in max_limits and job.cpu:
            cpu_max = max_limits["cpu"]
            if utils.parse_quantity(job.cpu) > utils.parse_quantity(cpu_max):
                raise Exception(
                    f"Requested CPU {job.cpu} is over maximum allowed per container ({cpu_max})"
                )

        if "memory" in max_limits and job.memory:
            memory_max = max_limits["memory"]
            if utils.parse_quantity(job.memory) > utils.parse_quantity(memory_max):
                raise Exception(
                    f"Requested memory {job.memory} is over maximum"
                    + f"allowed per container ({memory_max})"
                )


def create_job(user: User, job: Job):
    validate_job_limits(user, job)
    return user.kapi.create_object(job.k8s_type, job.get_k8s_object())


def delete_job(user: User, jobname: str):
    try:
        validate_jobname(jobname)
    except Exception:
        # invalid job name, ignore
        return

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
    try:
        validate_jobname(jobname)
    except Exception:
        # invalid job name, ignore
        return []

    job_list = []

    for kind in ["jobs", "cronjobs", "deployments"]:
        selector = labels_selector(jobname=jobname, username=user.name, type=kind)
        for k8s_obj in user.kapi.get_objects(kind, selector=selector):
            job = Job.from_k8s_object(object=k8s_obj, kind=kind)
            refresh_job_short_status(user, job)
            refresh_job_long_status(user, job)
            job_list.append(job)

    return job_list


def _wait_for_pod_exit(user: User, job: Job, timeout: int = 30):
    """Wait for all pods belonging to a specific job to exit."""
    selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)

    for _ in range(timeout * 2):
        pods = user.kapi.get_objects("pods", selector=selector)
        if len(pods) == 0:
            return True
        time.sleep(0.5)
    return False


def _launch_manual_cronjob(user: User, job: Job):
    validate_job_limits(user, job)

    cronjob = user.kapi.get_object("cronjobs", job.jobname)
    metadata = utils.dict_get_object(cronjob, "metadata")

    user.kapi.create_object("jobs", job.get_k8s_single_run_object(metadata["uid"]))


def restart_job(user: User, job: Job):
    selector = labels_selector(job.jobname, user.name, job.k8s_type)

    if job.k8s_type == "cronjobs":
        if not user.kapi.get_objects("jobs", selector=selector):
            raise Exception("job is currently not running")

        # Delete currently running jobs to avoid duplication
        user.kapi.delete_objects("jobs", selector=selector)
        user.kapi.delete_objects("pods", selector=selector)

        # Wait until the currently running job stops
        _wait_for_pod_exit(user, job)

        # Launch it manually
        _launch_manual_cronjob(user, job)
    elif job.k8s_type == "deployments":
        # Simply delete the pods and let Kubernetes re-create them
        user.kapi.delete_objects("pods", selector=selector)
    elif job.k8s_type == "jobs":
        raise Exception("single jobs can't be restarted")
    else:
        raise Exception(f"couldn't restart unknown job type: {job}")
