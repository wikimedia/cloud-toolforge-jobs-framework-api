from tjf.labels import labels_selector
from tjf.job import Job
from tjf.user import User
import tjf.utils as utils


def create_job(user: User, job: Job):
    return user.kapi.create_object(job.k8s_type, job.get_k8s_object())


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
        for k8s_obj in user.kapi.get_objects(kind, selector=selector):
            job = Job.from_k8s_object(object=k8s_obj, kind=kind)
            refresh_job_status(user, job)
            job_list.append(job)

    return job_list


def _pods_in_phase(podlist, phase):
    ret = 0
    for pod in podlist:
        if pod["status"]["phase"] == phase:
            ret += 1

    return ret


def _pods_phase_report(job: Job, podlist: list):
    n = len(podlist)
    if n == 0:
        job.status["long"] = "No additional information until next execution."
        return
    else:
        job.status["long"] = f"There are {n} pods for this job."

    for phase in ["Running", "Pending", "Failed", "Succeeded", "Terminating"]:
        n = _pods_in_phase(podlist, phase)
        if n > 0:
            job.status["long"] += f" {n} pods in '{phase}' state."


def _refresh_status_cronjob(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    last = status_dict.get("lastScheduleTime", "unknown")
    job.status["short"] = f"Last schedule time: {last}"

    selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
    podlist = user.kapi.get_objects("pods", selector=selector)

    _pods_phase_report(job, podlist)

    for pod in podlist:
        # try to provide some hint, search for pods in the Failed state.
        if pod["status"]["phase"] != "Failed":
            continue

        for containerstatus in pod["status"]["containerStatuses"]:
            hint = containerstatus["state"]
            job.status["long"] += f" Additional hints from the kubernetes backend: {hint}"
            # just one container. In general we just create 1 container per pod here
            break

        # just one is fine, we tried configuring the cronjob to only have 1 pod anyway
        break


def _refresh_status_dp(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Available":
            if condition["status"] == "True":
                job.status["short"] = "Running"
            elif condition["status"] == "False":
                job.status["short"] = "Not running"

    selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
    podlist = user.kapi.get_objects("pods", selector=selector)

    _pods_phase_report(job, podlist)

    for pod in podlist:
        # try to provide some additional hint
        if pod["status"]["phase"] == "Running":
            for containerstatus in pod["status"]["containerStatuses"]:
                if not containerstatus["ready"]:
                    job.status["long"] += " Pod not ready."

                restartcount = containerstatus["restartCount"]
                if restartcount > 0:
                    job.status["long"] += f" Pod has been restarted {restartcount} times."

                lastState = containerstatus["lastState"]
                terminated = lastState.get("terminated", None)
                if terminated:
                    reason = terminated.get("reason", "unknown")
                    retcode = terminated.get("exitCode", "unknown")
                    job.status[
                        "long"
                    ] += f" Pod terminated because reason '{reason}' with exitcode '{retcode}'"

                # just one container. In general we just create 1 container per pod here
                break
        # just one is fine, we configured the deployment to only have 1 pod anyway
        break


def _refresh_status_job(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Complete":
            if condition["status"] == "True":
                job.status["short"] = "Completed"
            elif condition["status"] == "False":
                job.status["short"] = "Not running"

    # no conditions?
    if len(conditions_dict) == 0 and status_dict.get("failed", None) is not None:
        job.status["short"] = "Failed"

    selector = labels_selector(jobname=job.jobname, username=user.name, type=job.k8s_type)
    podlist = user.kapi.get_objects("pods", selector=selector)

    _pods_phase_report(job, podlist)

    if status_dict.get("active", 0) == 1:
        starttime = status_dict["startTime"]
        job.status["long"] += f" Last run attempt at {starttime}."

    for pod in podlist:
        if pod.get("status", None) is None:
            continue

        for containerstatus in pod["status"].get("containerStatuses", []):
            states = containerstatus.get("state", None)
            for state in states:
                msg = containerstatus["state"][state].get("message", "unknown")
                job.status["long"] += f" State '{state}' for reason '{msg}'."


def refresh_job_status(user: User, job: Job):
    if job.k8s_type == "cronjobs":
        _refresh_status_cronjob(user, job)
    elif job.k8s_type == "deployments":
        _refresh_status_dp(user, job)
    elif job.k8s_type == "jobs":
        _refresh_status_job(user, job)
    else:
        raise Exception(f"couldn't refresh status for unknown job type: {job}")
