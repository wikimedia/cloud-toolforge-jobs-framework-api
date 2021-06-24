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
            refresh_job_short_status(user, job)
            refresh_job_long_status(user, job)
            job_list.append(job)

    return job_list


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


def _refresh_status_job(user: User, job: Job):
    status_dict = utils.dict_get_object(job.k8s_object, "status")
    conditions_dict = status_dict.get("conditions", [])
    for condition in conditions_dict:
        if condition["type"] == "Complete":
            if condition["status"] == "True":
                job.status_short = "Completed"
            elif condition["status"] == "False":
                job.status_short = "Not running"

    # no conditions?
    if job.status_short == "Unknown" and status_dict.get("failed", None) is not None:
        job.status_short = "Failed"


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

    # we only have 1 container per pod
    containerstatus = pod["status"].get("containerStatuses", [])[0]
    if containerstatus is None:
        # nothing else to report
        return

    restartcount = containerstatus["restartCount"]
    if restartcount > 0:
        job.status_long += f" Pod has been restarted {restartcount} times."

    # the pod didn't have a lastState, is currently live! (failing or not)
    currentstate = containerstatus["state"]

    # please python, I just need the key as a string
    for c in currentstate:
        state = c
        break

    reason = containerstatus["state"][state].get("reason", "unknown")
    job.status_long += f" State '{state}' for reason '{reason}'."

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
