import pytest
import tests.fake_k8s as fake_k8s
from common.k8sclient import K8sClient
from tjf.images import image_get_url, update_available_images, AVAILABLE_IMAGES


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
                        "images-v1.yaml": fake_k8s.fake_images,
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
    ["name", "expected"],
    [
        ["node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
        ["tf-node12", "docker-registry.tools.wmflabs.org/toolforge-node12-sssd-base:latest"],
        ["php7.3", "docker-registry.tools.wmflabs.org/toolforge-php73-sssd-base:latest"],
    ],
)
def test_image_get_url(images_available, name, expected):
    """Basic test for the image_get_url() func."""
    assert image_get_url(name) == expected
