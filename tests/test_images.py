import pytest
from common.k8sclient import K8sClient
from tests.fake_k8s import FAKE_HARBOR_HOST, FAKE_IMAGE_CONFIG
from tjf.app import create_app
from tjf.images import (
    image_by_name,
    update_available_images,
    image_by_container_url,
    AVAILABLE_IMAGES,
)


@pytest.fixture
def fake_k8s_client(monkeypatch):
    class FakeClient:
        def __init__(self, *, namespace: str):
            pass

        def get_object(self, kind, name):
            if kind == "configmaps" and name == "image-config":
                return {
                    "kind": "ConfigMap",
                    "apiVersion": "v1",
                    # spec omitted, since it's not really relevant
                    "data": {
                        "images-v1.yaml": FAKE_IMAGE_CONFIG,
                    },
                }

    monkeypatch.setattr(K8sClient, "from_container_service_account", FakeClient)


@pytest.fixture
def images_available(fake_k8s_client, fake_harbor_api):
    update_available_images()


def test_available_images_len(images_available):
    """Basic test to check if the available images dictionary was updated."""
    assert len(AVAILABLE_IMAGES) > 1


IMAGE_NAME_TESTS = [
    ["node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
    ["tf-node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
    ["php7.3", "docker-registry.tools.wmflabs.org/toolforge-php73-sssd-base:latest"],
    [
        "tool-some-tool/some-container:latest",
        f"{FAKE_HARBOR_HOST}/tool-some-tool/some-container:latest",
    ],
    [
        "tool-some-tool/some-container:stable",
        f"{FAKE_HARBOR_HOST}/tool-some-tool/some-container:stable",
    ],
    ["tool-other/tagged:example", f"{FAKE_HARBOR_HOST}/tool-other/tagged:example"],
]


@pytest.mark.parametrize(
    ["name", "url"],
    IMAGE_NAME_TESTS,
)
def test_image_by_name(images_available, name, url):
    """Basic test for the image_by_name() func."""
    assert image_by_name(name).container == url


@pytest.mark.parametrize(
    ["name", "url"],
    IMAGE_NAME_TESTS,
)
def test_image_by_container_url(images_available, name, url):
    """Basic test for the image_by_container_url() func."""
    image = image_by_container_url(url)
    assert image is not None
    assert image.canonical_name == name or name in image.aliases


@pytest.fixture()
def client(fake_k8s_client):
    return create_app().test_client()


def test_get_images_endpoint(images_available, client, fake_user):
    response = client.get("/api/v1/images/", headers=fake_user)
    assert response.status_code == 200

    image_names = [image["shortname"] for image in response.json]
    assert "node16" in image_names

    assert "php7.4" in image_names
    assert "tf-php74" not in image_names
    assert "php7.3" not in image_names

    assert "tool-some-tool/some-container:latest" in image_names
    assert "tool-some-tool/some-container:stable" in image_names
    # other tools are not listed here
    assert "tool-other/tagged:example" not in image_names
