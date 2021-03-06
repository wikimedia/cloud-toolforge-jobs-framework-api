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
from decimal import Decimal, InvalidOperation  # for parse_quantity below


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

    raise Exception(f"{string} is not a valid Kubernetes quantity")


# Copyright 2019 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


def parse_quantity(quantity):
    """
    Parse kubernetes canonical form quantity like 200Mi to a decimal number.
    Supported SI suffixes:
    base1024: Ki | Mi | Gi | Ti | Pi | Ei
    base1000: n | u | m | "" | k | M | G | T | P | E

    See https://github.com/kubernetes/apimachinery/blob/master/pkg/api/resource/quantity.go # noqa

    Input:
    quanity: string. kubernetes canonical form quantity

    Returns:
    Decimal

    Raises:
    ValueError on invalid or unknown input
    """
    if isinstance(quantity, (int, float, Decimal)):
        return Decimal(quantity)

    exponents = {
        "n": -3,
        "u": -2,
        "m": -1,
        "K": 1,
        "k": 1,
        "M": 2,
        "G": 3,
        "T": 4,
        "P": 5,
        "E": 6,
    }

    quantity = str(quantity)
    number = quantity
    suffix = None
    if len(quantity) >= 2 and quantity[-1] == "i":
        if quantity[-2] in exponents:
            number = quantity[:-2]
            suffix = quantity[-2:]
    elif len(quantity) >= 1 and quantity[-1] in exponents:
        number = quantity[:-1]
        suffix = quantity[-1:]

    try:
        number = Decimal(number)
    except InvalidOperation:
        raise ValueError("Invalid number format: {}".format(number))

    if suffix is None:
        return number

    if suffix.endswith("i"):
        base = 1024
    elif len(suffix) == 1:
        base = 1000
    else:
        raise ValueError("{} has unknown suffix".format(quantity))

    # handly SI inconsistency
    if suffix == "ki":
        raise ValueError("{} has unknown suffix".format(quantity))

    if suffix[0] not in exponents:
        raise ValueError("{} has unknown suffix".format(quantity))

    exponent = Decimal(exponents[suffix[0]])
    return number * (base ** exponent)
