# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass
from typing import List, ClassVar


@dataclass(frozen=True)
class Command:
    """Class to represenet a job command."""

    _WRAPPER: ClassVar[List[str]] = ["/bin/sh", "-c", "--"]
    _STDOUT_PREFIX: ClassVar[str] = "exec 1>>"
    _STDERR_PREFIX: ClassVar[str] = "exec 2>>"

    user_command: str
    filelog: bool
    filelog_stdout: str
    filelog_stderr: str

    def generate_for_k8s(self) -> List[str]:
        """Generate the command array for the kubernetes object."""
        ret = self._WRAPPER.copy()

        command = ""
        command += f"{self._STDOUT_PREFIX}{self.filelog_stdout};"
        command += f"{self._STDERR_PREFIX}{self.filelog_stderr};"
        command += f"{self.user_command}"

        ret.append(command)

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
        labels = k8s_metadata["labels"]

        _filelog = labels.get("jobs.toolforge.org/filelog", "no")
        if _filelog == "yes":
            filelog = True
        else:
            filelog = False

        command_spec = k8s_command[-1]
        command_new_format = labels.get("jobs.toolforge.org/command-new-format", "no")
        if command_new_format == "yes":
            items = command_spec.split(";")
            # support user-specied command in the form 'x ; y ; z'
            user_command = ";".join(items[2:])
        else:
            user_command = command_spec[: command_spec.rindex(" 1>")]

        # anyway, failsafe. If we failed to parse something, show something to users.
        if user_command == "":
            user_command = "unknown"

        if filelog:
            filelog_stdout = f"{jobname}.out"
            filelog_stderr = f"{jobname}.err"
        else:
            filelog_stdout = "/dev/null"
            filelog_stderr = "/dev/null"

        return cls(
            user_command=user_command,
            filelog=filelog,
            filelog_stdout=filelog_stdout,
            filelog_stderr=filelog_stderr,
        )
