# SPDX-License-Identifier: AGPL-3.0-or-later

import shlex
from dataclasses import dataclass
from typing import List, ClassVar, Optional


@dataclass(frozen=True)
class GeneratedCommand:
    command: List[str]
    args: Optional[List[str]]


@dataclass(frozen=True)
class Command:
    """Class to represenet a job command."""

    _WRAPPER: ClassVar[List[str]] = ["/bin/sh", "-c", "--"]
    _STDOUT_PREFIX: ClassVar[str] = "exec 1>>"
    _STDERR_PREFIX: ClassVar[str] = "exec 2>>"

    user_command: str
    use_wrapper: bool
    filelog: bool
    filelog_stdout: Optional[str]
    filelog_stderr: Optional[str]

    def generate_for_k8s(self) -> GeneratedCommand:
        """Generate the command array for the kubernetes object."""
        if not self.use_wrapper:
            splitted = shlex.split(self.user_command)
            return GeneratedCommand(command=[splitted[0]], args=splitted[1:])

        ret = self._WRAPPER.copy()

        command = ""
        if self.filelog_stdout is not None:
            command += f"{self._STDOUT_PREFIX}{self.filelog_stdout};"
        if self.filelog_stderr is not None:
            command += f"{self._STDERR_PREFIX}{self.filelog_stderr};"
        command += f"{self.user_command}"

        ret.append(command)

        return GeneratedCommand(command=ret, args=None)

    @classmethod
    def from_api(
        cls,
        *,
        user_command: str,
        use_wrapper: bool,
        filelog: bool,
        filelog_stdout: Optional[str],
        filelog_stderr: Optional[str],
        jobname: str,
    ) -> "Command":
        """Create a new Command class instance from TJF API parameters."""
        if filelog:
            actual_filelog_stdout = filelog_stdout if filelog_stdout else f"{jobname}.out"
            actual_filelog_stderr = filelog_stderr if filelog_stderr else f"{jobname}.err"
        else:
            actual_filelog_stdout = None
            actual_filelog_stderr = None

        return cls(
            user_command=user_command,
            use_wrapper=use_wrapper,
            filelog=filelog,
            filelog_stdout=actual_filelog_stdout,
            filelog_stderr=actual_filelog_stderr,
        )

    @classmethod
    def from_k8s(
        cls, *, k8s_metadata: dict, k8s_command: List[str], k8s_arguments: Optional[List[str]]
    ) -> "Command":
        """Parse from kubernetes object and return a new Command class instance."""
        jobname = k8s_metadata["name"]
        labels = k8s_metadata["labels"]

        filelog = labels.get("jobs.toolforge.org/filelog", "no") == "yes"

        job_version = int(labels.get("app.kubernetes.io/version", "1"))

        command_spec = k8s_command[-1]
        command_new_format = (
            labels.get(
                "jobs.toolforge.org/command-new-format", ("no" if job_version == 1 else "yes")
            )
            == "yes"
        )

        if command_new_format:
            if filelog or job_version == 1:
                use_wrapper = True
                items = command_spec.split(";")
                # support user-specied command in the form 'x ; y ; z'
                user_command = ";".join(items[2:])
                filelog_stdout = items[0].replace(cls._STDOUT_PREFIX, "")
                filelog_stderr = items[1].replace(cls._STDERR_PREFIX, "")
            else:
                if len(k8s_command) == len(cls._WRAPPER) + 1 and k8s_command[:-1] == cls._WRAPPER:
                    use_wrapper = True
                    user_command = command_spec
                else:
                    use_wrapper = False
                    user_command = shlex.join(k8s_command + k8s_arguments)

                filelog_stdout = None
                filelog_stderr = None
        else:
            user_command = command_spec[: command_spec.rindex(" 1>")]
            use_wrapper = True
            # there can't be jobs with the old command array layout with custom logfiles, so this
            # is rather simple
            if filelog:
                filelog_stdout = f"{jobname}.out"
                filelog_stderr = f"{jobname}.err"
            else:
                filelog_stdout = "/dev/null"
                filelog_stderr = "/dev/null"

        # anyway, failsafe. If we failed to parse something, show something to users.
        if user_command == "":
            user_command = "unknown"

        return cls(
            user_command=user_command,
            use_wrapper=use_wrapper,
            filelog=filelog,
            filelog_stdout=filelog_stdout,
            filelog_stderr=filelog_stderr,
        )
