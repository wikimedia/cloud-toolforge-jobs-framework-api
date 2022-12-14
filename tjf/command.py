# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from typing import List, ClassVar


def _remove_filelog_suffix(command: str) -> str:
    # remove log substring, which should be the last thing in the command string
    return command[: command.rindex(" 1>")]


@dataclass(frozen=True)
class Command:
    """Class to represenet a job command."""

    _WRAPPER_START: ClassVar[List[str]] = ["/bin/sh", "-c"]
    _WRAPPER_END: ClassVar[str] = "--"

    user_command: str
    filelog: bool
    filelog_stdout: str
    filelog_stderr: str

    def generate_for_k8s(self) -> List[str]:
        """Generate the command array for the kubernetes object."""
        ret = self._WRAPPER_START.copy()  # indexes 0,1
        ret.append(f"1>>{self.filelog_stdout}")  # index 2
        ret.append(f"2>>{self.filelog_stderr}")  # index 3
        ret.append(self._WRAPPER_END)  # index 4
        ret.append(self.user_command)  # index 5 (or -1)
        return ret

    @classmethod
    def from_api(cls, user_command: str, filelog: bool, jobname: str) -> "Command":
        """Create a new Command class instance from TJF API parameters."""
        if not filelog:
            actual_filelog_stdout = "/dev/null"
            actual_filelog_stderr = "/dev/null"
        else:
            actual_filelog_stdout = f"{jobname}.out"
            actual_filelog_stderr = f"{jobname}.err"

        return cls(
            user_command=user_command,
            filelog=filelog,
            filelog_stdout=actual_filelog_stdout,
            filelog_stderr=actual_filelog_stderr,
        )

    @classmethod
    def from_k8s(cls, k8s_metadata: dict, k8s_command: List[str]) -> "Command":
        """Parse from kubernetes object and return a new Command class instance."""
        jobname = k8s_metadata["name"]

        _filelog = k8s_metadata["labels"].get("jobs.toolforge.org/filelog", "no")
        if _filelog == "yes":
            filelog = True
        else:
            filelog = False

        # remember: the original user command is in the last item of the k8s command array
        k8s_command_array_len = len(k8s_command)

        if k8s_command_array_len == 4:
            # this means the command array is old. The filelog redirections are embedded in the
            # user command. Eventually this branch can be removed, when we're sure no jobs exists
            # with this old layout
            user_command = _remove_filelog_suffix(k8s_command[-1])
            if filelog:
                filelog_stdout = f"{jobname}.out"
                filelog_stderr = f"{jobname}.err"
            else:
                filelog_stdout = "/dev/null"
                filelog_stderr = "/dev/null"
        elif k8s_command_array_len == 6:
            # this means the command array is modern. The filelog redirections are NOT embedded in
            # the user command
            user_command = k8s_command[-1]
            filelog_stdout = k8s_command[2].replace("1>>", "")
            filelog_stderr = k8s_command[3].replace("2>>", "")
        else:
            # anyway, failsafe. If we failed to parse something, show something to users.
            user_command = "unknown"
            filelog_stdout = "unknown"
            filelog_stderr = "unknown"

        return cls(
            user_command=user_command,
            filelog=filelog,
            filelog_stdout=filelog_stdout,
            filelog_stderr=filelog_stderr,
        )
