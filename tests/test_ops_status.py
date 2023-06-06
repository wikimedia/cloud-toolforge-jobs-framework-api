import pytest
import tests.fake_k8s as fake_k8s
from tjf.job import Job
from tjf.ops_status import _get_quota_error, refresh_job_short_status


def test_get_quota_error():
    message = 'Error creating: pods "test2-dgggb" is forbidden: exceeded quota: tool-tf-test, requested: limits.cpu=500m,limits.memory=512Mi, used: limits.cpu=1,limits.memory=1Gi, limited: limits.cpu=100m,limits.memory=12'  # noqa: E501
    assert _get_quota_error(message) == "out of quota for cpu, memory"


@pytest.mark.parametrize(
    "cronjob, job, status_short",
    [
        [fake_k8s.CRONJOB_NOT_RUN_YET, {}, "Waiting for scheduled time"],
        [fake_k8s.CRONJOB_NOT_RUN_YET, fake_k8s.JOB_FROM_A_CRONJOB_RESTART, "Running for "],
        [fake_k8s.CRONJOB_WITH_RUNNING_JOB, fake_k8s.JOB_FROM_A_CRONJOB_RESTART, "Running for "],
        [fake_k8s.CRONJOB_WITH_RUNNING_JOB, fake_k8s.JOB_FROM_A_CRONJOB, "Running for "],
        [fake_k8s.CRONJOB_WITH_RUNNING_JOB, {}, "Last schedule time: 2023-04-13T15:05:00Z"],
        [
            fake_k8s.CRONJOB_PREVIOUS_RUN_BUT_NO_RUNNING_JOB,
            {},
            "Last schedule time: 2023-04-13T14:55:00Z",
        ],
    ],
)
def test_refresh_job_short_status_cronjob(cronjob, job, status_short):
    def setup_user():
        class FakeK8sApi:
            def get_objects(self, kind, *, label_selector):
                if kind == "jobs":
                    return [job]
                raise Exception("not supposed to happen")

            def get_object(self, kind, name):
                if kind == "jobs":
                    return job
                raise Exception("not supposed to happen")

        class FakeUser:
            name = "tf-test"
            namespace = "tool-tf-test"
            kapi = FakeK8sApi()

        return FakeUser()

    user = setup_user()
    _job = Job.from_k8s_object(cronjob, "cronjobs")
    refresh_job_short_status(user, _job)
    assert status_short in _job.status_short
