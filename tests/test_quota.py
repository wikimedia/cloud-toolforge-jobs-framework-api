# Copyright (C) 2023 Taavi Väänänen <hi@taavi.wtf>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
from pathlib import Path
from typing import Dict
import pytest
from flask.testing import FlaskClient
from tjf.app import create_app
from tjf.user import User


@pytest.fixture
def client() -> FlaskClient:
    return create_app(load_images=False).test_client()


@pytest.fixture
def user_with_quotas(fixtures_path: Path):
    class FakeK8sApi:
        def get_object(self, kind, name):
            if kind == "limitranges" and name == "tool-some-tool":
                return json.loads((fixtures_path / "quota" / "limitrange.json").read_text())
            elif kind == "resourcequotas" and name == "tool-some-tool":
                return json.loads((fixtures_path / "quota" / "resourcequota.json").read_text())
            raise Exception("not supposed to happen")

    class FakeUser:
        name = "some-tool"
        namespace = "tool-some-tool"
        kapi = FakeK8sApi()

    return FakeUser()


@pytest.fixture
def patch_user_to_have_quotas(user_with_quotas, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(User, "from_request", lambda: user_with_quotas)


def test_quota_endpoint(
    client: FlaskClient, fixtures_path: Path, patch_user_to_have_quotas, fake_user: Dict[str, str]
):
    expected = json.loads((fixtures_path / "quota" / "expected-api-result.json").read_text())
    response = client.get("/api/v1/quota/", headers=fake_user)

    assert response.status_code == 200
    assert response.json == expected
