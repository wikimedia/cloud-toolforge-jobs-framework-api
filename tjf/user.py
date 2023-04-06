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

import os
import yaml
from flask import request
from cryptography import x509
from common.k8sclient import K8sClient
from tjf.error import TjfClientError


AUTH_HEADER = "ssl-client-subject-dn"


class UserLoadingError(TjfClientError):
    """Custom error class for exceptions related to loading user data."""

    http_status_code = 403


class User:
    def __init__(self, name):
        self.name = name
        self.namespace = f"tool-{self.name}"

        # TODO: fetch this from LDAP instead?
        self.home = f"/data/project/{name}"

        self.kubeconfig_path = os.path.join(self.home, ".kube", "config")
        self.validate_kubeconfig()
        self.kapi = K8sClient.from_file(filename=self.kubeconfig_path)

    def validate_kubeconfig(self):
        path = self.kubeconfig_path

        try:
            with open(path) as file:
                config = yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"couldn't read kubeconfig for user '{self.name}': {e}")

        if config is None:
            raise Exception(f"user file '{path}' is empty")

        # copied from maintain_kubeusers :-P
        if all(
            k in config
            for k in (
                "apiVersion",
                "kind",
                "clusters",
                "users",
                "contexts",
                "current-context",
            )
        ):
            return config
        else:
            raise Exception(f"invalid kubeconfig for user '{self.name}'")

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
