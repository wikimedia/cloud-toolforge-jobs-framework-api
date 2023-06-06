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

import re
from typing import Set

from tjf.error import TjfValidationError


USER_AGENT = "jobs-api"

KUBERNETES_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def dict_get_object(dict, kind):
    for o in dict:
        if o == kind:
            return dict[o]


# copied & adapted from toollabs-webservice scripts/webservice
def validate_kube_quant(string: str):
    """
    A type for args that roughly matches up with Kubernetes' quantity.go
    General form is <number><suffix>
    The following are acceptable suffixes

    base1024: Ki | Mi | Gi | Ti | Pi | Ei
    base1000: n | u | m | "" | k | M | G | T | P | E
    """
    if string is None or string == "":
        return  # nothing to validate

    valid_suffixes = [
        "Ki",
        "Mi",
        "Gi",
        "Ti",
        "Pi",
        "Ei",
        "n",
        "u",
        "m",
        "",
        "k",
        "M",
        "G",
        "T",
        "P",
        "E",
    ]
    pattern = re.compile(r"^(\d+)([A-Za-z]{0,2})$")
    quant_check = pattern.match(string)
    if quant_check:
        suffix = quant_check.group(2)
        if suffix in valid_suffixes:
            return string

    raise TjfValidationError(f"{string} is not a valid Kubernetes quantity")


def format_duration(seconds: int) -> int:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    value = ""
    if d > 0:
        value += f"{d}d"
    if h > 0:
        value += f"{h}h"
    if m > 0:
        value += f"{m}m"
    if (s > 0 and d == 0) or value == "":
        value += f"{s}s"
    return value


def remove_prefixes(text: str, prefixes: Set[str]) -> str:
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text
