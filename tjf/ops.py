from tjf.labels import labels_selector
from tjf.job import Job
from tjf.user import User


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
        for job in user.kapi.get_objects(kind, selector=selector):
            job_list.append(Job.from_k8s_object(object=job, kind=kind))

    return job_list
