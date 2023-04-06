import pytest
from tjf.app import create_app
from tjf.user import AUTH_HEADER, User, UserLoadingError


@pytest.fixture()
def app():
    return create_app(load_images=False)


def test_User_from_request_successful(app, patch_kube_config_loading):
    with app.test_request_context("/foo", headers={AUTH_HEADER: "O=toolforge,CN=some-tool"}):
        user = User.from_request()

    assert user.name == "some-tool"
    assert user.namespace == "tool-some-tool"


def test_User_from_request_no_header(app, patch_kube_config_loading):
    with app.test_request_context("/foo"):
        with pytest.raises(UserLoadingError, match="missing 'ssl-client-subject-dn' header"):
            assert User.from_request() is None


invalid_cn_data = [
    [None, "Failed to parse certificate name 'None'"],
    ["", "Failed to parse certificate name ''"],
    ["O=toolforge", "Failed to load name for certificate 'O=toolforge'"],
    ["CN=first,CN=second", "Failed to load name for certificate 'CN=first,CN=second'"],
    [
        "CN=tool,O=admins",
        r"This certificate can't access the Jobs API\. "
        r"Double check you're logged in to the correct account\? \(got \[\'admins\'\]\)",
    ],
]


@pytest.mark.parametrize(
    "cn,expected_error", invalid_cn_data, ids=[data[0] for data in invalid_cn_data]
)
def test_User_from_request_invalid(app, patch_kube_config_loading, cn, expected_error):
    with app.test_request_context("/foo", headers={AUTH_HEADER: cn}):
        with pytest.raises(UserLoadingError, match=expected_error):
            assert User.from_request() is None
