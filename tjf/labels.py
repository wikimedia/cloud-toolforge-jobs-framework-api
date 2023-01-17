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


def generate_labels(
    jobname: str,
    username: str,
    type: str,
    filelog: bool,
    emails: str,
    command_new_format: bool = True,
):
    obj = {
        "toolforge": "tool",
        "app.kubernetes.io/version": "1",
        "app.kubernetes.io/managed-by": "toolforge-jobs-framework",
        "app.kubernetes.io/created-by": username,
    }

    if type is not None:
        obj["app.kubernetes.io/component"] = type

    if jobname is not None:
        obj["app.kubernetes.io/name"] = jobname

    if filelog is True:
        obj["jobs.toolforge.org/filelog"] = "yes"

    if emails is not None:
        obj["jobs.toolforge.org/emails"] = emails

    if command_new_format:
        # temporal label, until no jobs without it exist
        obj["jobs.toolforge.org/command-new-format"] = "yes"

    return obj


def labels_selector(jobname: str, username: str, type: str):
    return ",".join(
        [
            "{k}={v}".format(k=k, v=v)
            for k, v in generate_labels(
                jobname=jobname,
                username=username,
                type=type,
                filelog=False,
                emails=None,
                command_new_format=False,
            ).items()
        ]
    )
