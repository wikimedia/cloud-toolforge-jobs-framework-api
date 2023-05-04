import pytest
from common.k8sclient import K8sClient
from tests.fake_k8s import FAKE_IMAGE_CONFIG
from tjf.app import create_app
from tjf.images import image_by_name, update_available_images, AVAILABLE_IMAGES


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
def images_available(fake_k8s_client):
    update_available_images()


def test_available_images_len(images_available):
    """Basic test to check if the available images dictionary was updated."""
    assert len(AVAILABLE_IMAGES) > 1


@pytest.mark.parametrize(
    ["name", "url"],
    [
        ["node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
        ["tf-node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
        ["php7.3", "docker-registry.tools.wmflabs.org/toolforge-php73-sssd-base:latest"],
    ],
)
def test_image_by_name(images_available, name, url):
    """Basic test for the image_by_name() func."""
    assert image_by_name(name).container == url


@pytest.fixture()
def client(fake_k8s_client):
    return create_app().test_client()


def test_get_images_endpoint(client, fake_user):
    response = client.get("/api/v1/images/", headers=fake_user)
    assert response.status_code == 200

    image_names = [image["shortname"] for image in response.json]
    assert "node16" in image_names

    assert "php7.4" in image_names
    assert "tf-php74" not in image_names
    assert "php7.3" not in image_names
