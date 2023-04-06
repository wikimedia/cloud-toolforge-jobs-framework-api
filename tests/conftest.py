import pytest
from common.k8sclient import K8sClient

from tjf.user import AUTH_HEADER, User


FAKE_VALID_TOOL_AUTH_HEADER = "O=toolforge,CN=some-tool"


@pytest.fixture(scope="module")
def monkeymodule():
    """Needed to use monkeypatch at module scope."""
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="module")
def patch_kube_config_loading(monkeymodule):
    def noop(*args, **kwargs):
        return True

    monkeymodule.setattr(User, "validate_kubeconfig", noop)
    monkeymodule.setattr(K8sClient, "from_file", noop)


@pytest.fixture(scope="module")
def fake_user(patch_kube_config_loading):
    yield {AUTH_HEADER: FAKE_VALID_TOOL_AUTH_HEADER}
