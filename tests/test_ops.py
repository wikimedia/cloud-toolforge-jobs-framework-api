import pytest

from tests.fake_k8s import LIMIT_RANGE_OBJECT, FakeJob
from tjf.ops import validate_job_limits


@pytest.fixture()
def user_with_limit_range():
    class FakeK8sApi:
        def get_object(self, kind, name):
            if kind == "limitranges" and name == "tool-test-tool":
                return LIMIT_RANGE_OBJECT
            raise Exception("not supposed to happen")

    class FakeUser:
        name = "test-tool"
        namespace = "tool-test-tool"
        kapi = FakeK8sApi()

    return FakeUser()


def test_validate_job_limits_default_job(user_with_limit_range):
    job_with_defaults = FakeJob()
    assert validate_job_limits(user_with_limit_range, job_with_defaults) is None


def test_validate_job_limits_custom(user_with_limit_range):
    job = FakeJob(cpu="0.5", memory="1Gi")
    assert validate_job_limits(user_with_limit_range, job) is None


def test_validate_job_limits_under_minimum(user_with_limit_range):
    job = FakeJob(memory="50Mi")

    with pytest.raises(
        Exception,
        match="Requested memory 50Mi is less than minimum required per container \\(100Mi\\)",
    ):
        validate_job_limits(user_with_limit_range, job)


def test_validate_job_limits_over_maximum(user_with_limit_range):
    job = FakeJob(cpu="2.5")

    with pytest.raises(
        Exception,
        match="Requested CPU 2.5 is over maximum allowed per container \\(1\\)",
    ):
        validate_job_limits(user_with_limit_range, job)
