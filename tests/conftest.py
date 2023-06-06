import json
from pathlib import Path

import requests_mock
import pytest
from toolforge_weld.kubernetes_config import Kubeconfig, fake_kube_config

from tests.fake_k8s import FAKE_HARBOR_HOST
import tjf.images
from tjf.user import AUTH_HEADER
from tjf.images import HarborConfig


FAKE_VALID_TOOL_AUTH_HEADER = "O=toolforge,CN=some-tool"

FIXTURES_PATH = Path(__file__).parent.resolve() / "helpers" / "fixtures"


@pytest.fixture(scope="module")
def monkeymodule():
    """Needed to use monkeypatch at module scope."""
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="module")
def requests_mock_module():
    with requests_mock.Mocker() as m:
        yield m


@pytest.fixture(scope="module")
def patch_kube_config_loading(monkeymodule):
    def load_fake(*args, **kwargs):
        return fake_kube_config()

    monkeymodule.setattr(Kubeconfig, "from_path", load_fake)


@pytest.fixture(scope="module")
def fake_user(patch_kube_config_loading):
    yield {AUTH_HEADER: FAKE_VALID_TOOL_AUTH_HEADER}


@pytest.fixture(scope="module")
def fake_harbor_api(monkeymodule, requests_mock_module):
    def fake_get_harbor_config() -> HarborConfig:
        return HarborConfig(
            host=FAKE_HARBOR_HOST,
        )

    monkeymodule.setattr(tjf.images, "get_harbor_config", fake_get_harbor_config)

    requests_mock_module.get(
        f"https://{FAKE_HARBOR_HOST}/api/v2.0/projects/tool-other/repositories/tagged/artifacts",
        json=json.loads((FIXTURES_PATH / "harbor" / "artifact-list-other.json").read_text()),
    )
    requests_mock_module.get(
        f"https://{FAKE_HARBOR_HOST}/api/v2.0/projects/tool-some-tool/repositories/some-container/artifacts",
        json=json.loads((FIXTURES_PATH / "harbor" / "artifact-list-some-tool.json").read_text()),
    )
    requests_mock_module.get(
        f"https://{FAKE_HARBOR_HOST}/api/v2.0/projects/tool-other/repositories",
        json=json.loads((FIXTURES_PATH / "harbor" / "repository-list-other.json").read_text()),
    )
    requests_mock_module.get(
        f"https://{FAKE_HARBOR_HOST}/api/v2.0/projects/tool-some-tool/repositories",
        json=json.loads((FIXTURES_PATH / "harbor" / "repository-list-some-tool.json").read_text()),
    )
