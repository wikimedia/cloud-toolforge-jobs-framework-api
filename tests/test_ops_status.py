from tjf.ops_status import _get_quota_error


def test_get_quota_error():
    message = 'Error creating: pods "test2-dgggb" is forbidden: exceeded quota: tool-tf-test, requested: limits.cpu=500m,limits.memory=512Mi, used: limits.cpu=1,limits.memory=1Gi, limited: limits.cpu=100m,limits.memory=12'  # noqa: E501
    assert _get_quota_error(message) == "out of quota for cpu, memory"
