# Copyright (C) 2021 Arturo Borrero Gonzalez <aborrero@wikimedia.org>
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
#

from pathlib import Path
from flask import request
from cryptography import x509
from toolforge_weld.kubernetes import K8sClient
from toolforge_weld.kubernetes_config import Kubeconfig
from tjf.error import TjfClientError
from tjf.utils import USER_AGENT


AUTH_HEADER = "ssl-client-subject-dn"


class UserLoadingError(TjfClientError):
    """Custom error class for exceptions related to loading user data."""

    http_status_code = 403


class User:
    def __init__(self, name):
        self.name = name
        self.namespace = f"tool-{self.name}"

        # TODO: fetch this from LDAP instead?
        self.home = Path(f"/data/project/{name}")

        self.kapi = K8sClient(
            kubeconfig=Kubeconfig.from_path(path=(self.home / ".kube" / "config")),
            user_agent=USER_AGENT,
        )

    @classmethod
    def from_request(self):
        if AUTH_HEADER not in request.headers:
            raise UserLoadingError(f"missing '{AUTH_HEADER}' header")

        # we are expecting something like 'CN=user,O=Toolforge'
        try:
            name_raw = request.headers.get(AUTH_HEADER)
            name = x509.Name.from_rfc4514_string(name_raw)
        except Exception as e:
            raise UserLoadingError(f"Failed to parse certificate name '{name_raw}'") from e

        cn = name.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        organizations = [
            attr.value for attr in name.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)
        ]

        if len(cn) != 1:
            raise UserLoadingError(f"Failed to load name for certificate '{name_raw}'")

        if organizations != ["toolforge"]:
            raise UserLoadingError(
                "This certificate can't access the Jobs API. "
                "Double check you're logged in to the correct account? "
                f"(got {organizations})"
            )

        common_name = cn[0].value
        return self(name=common_name)
