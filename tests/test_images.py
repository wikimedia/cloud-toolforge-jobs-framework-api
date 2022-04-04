import pytest
import mock
import json
import tests.fake_k8s as fake_k8s
from tests.context import (
    AVAILABLE_IMAGES,
    image_get_url,
    image_validate,
    image_get_shortname,
    update_available_images,
)


@pytest.fixture
def test_update_available_images():
    """Basic test for the update_available_images() func."""
    read_data = json.dumps(fake_k8s.fake_images)
    mock_open = mock.mock_open(read_data=read_data)
    with mock.patch("builtins.open", mock_open):
        update_available_images()


def test_available_images_len(test_update_available_images):
    """Basic test to check if the available images dictionary was updated."""
    assert len(AVAILABLE_IMAGES) > 1


def test_available_images_structure(test_update_available_images):
    """Basic test to check if the available images dict has the layout we want."""
    shortname = "tf-bullseye-std"
    url = "docker-registry.tools.wmflabs.org/toolforge-bullseye-standalone:latest"
    assert AVAILABLE_IMAGES[0]["shortname"] == shortname
    assert AVAILABLE_IMAGES[0]["image"] == url


def test_image_get_url(test_update_available_images):
    """Basic test for the image_get_url() func."""
    url = "docker-registry.tools.wmflabs.org/toolforge-bullseye-standalone:latest"
    assert image_get_url("tf-bullseye-std") == url


def test_image_validate(test_update_available_images):
    """Basic test for the image_validate() func."""
    assert image_validate("tf-golang111")


def test_image_get_shortname(test_update_available_images):
    """Basic test for the image_get_shortname() func."""
    url = "docker-registry.tools.wmflabs.org/toolforge-golang-sssd-base:latest"
    assert image_get_shortname(url) == "tf-golang"
