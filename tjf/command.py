# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from typing import List, ClassVar


def _filelog_string(jobname: str, filelog: bool):
    # Note that from_k8s_object() depends on the location of 1>>
    if filelog:
        return f" 1>>{jobname}.out 2>>{jobname}.err"

    return " 1>/dev/null 2>/dev/null"


def _remove_filelog_suffix(command: str) -> str:
    # remove log substring, which should be the last thing in the command string
    return command[: command.rindex(" 1>")]


@dataclass(frozen=True)
class Command:
    """Class to represenet a job command."""

    _WRAPPER: ClassVar[List[str]] = ["/bin/sh", "-c", "--"]

    user_command: str
    filelog: bool
    _jobname: str

    def generate_for_k8s(self) -> List[str]:
        """Generate the command array for the kubernetes object."""
        ret = self._WRAPPER.copy()
        ret.append(f"{self.user_command}{_filelog_string(self._jobname, self.filelog)}")
        return ret

    @classmethod
    def from_api(cls, user_command: str, filelog: bool, jobname: str) -> "Command":
        """Create a new Command class instance from TJF API parameters."""
        return cls(user_command=user_command, filelog=filelog, _jobname=jobname)

    @classmethod
    def from_k8s(cls, k8s_metadata: dict, k8s_command: List[str]) -> "Command":
        """Parse from kubernetes object and return a new Command class instance."""
        jobname = k8s_metadata["name"]

        _filelog = k8s_metadata["labels"].get("jobs.toolforge.org/filelog", "no")
        if _filelog == "yes":
            filelog = True
        else:
            filelog = False

        # the user specified command should be the last element in the cmd array
        _cmd = k8s_command[-1]
        cmd = _remove_filelog_suffix(_cmd)

        # if the job was created in the past with a different command format, we may have fail
        # to parse it. Show something to users
        if cmd is None or cmd == "":
            cmd = "unknown"

        return cls(user_command=cmd, filelog=filelog, _jobname=jobname)
