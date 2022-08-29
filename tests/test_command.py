import subprocess
from pathlib import Path
from typing import Optional

import pytest

import tests.fake_k8s as fake_k8s
import tjf.utils as utils
from tjf.command import Command


@pytest.mark.parametrize(
    "command, filelog, expected_stdout, expected_stderr",
    [
        # blank should never generate any output
        ["blank.sh", True, "", ""],
        ["blank.sh", False, None, None],
        # stdout only
        ["stdout.sh", True, "lorem\n", ""],
        ["stdout.sh", False, None, None],
        # stderr only
        ["stderr.sh", True, "", "ipsum\n"],
        ["stderr.sh", False, None, None],
        # both
        ["both.sh", True, "this text has no meaningful content,\n", "it is just an example\n"],
        ["both.sh", False, None, None],
    ],
)
def test_output_redirection(
    tmp_path_factory,
    command: str,
    filelog: bool,
    expected_stdout: Optional[str],
    expected_stderr: Optional[str],
):
    # this is provided by a pytest fixture, https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html
    directory = tmp_path_factory.mktemp("testcmd")

    script_path = Path(__file__).parent / "helpers" / "gen-output" / command

    cmd = Command.from_api(str(script_path.absolute()), filelog, "test.out", "test.err", "test")

    result = subprocess.run(cmd.generate_for_k8s(), capture_output=True, text=True, cwd=directory)

    # Everything is either saved to a file or discarded, nothing is printed to stdout or stderr.
    assert result.stdout == ""
    assert result.stderr == ""

    stdout_file = directory / "test.out"
    if stdout_file.exists():
        with stdout_file.open("r") as f:
            assert f.read() == expected_stdout
    else:
        assert expected_stdout is None

    stderr_file = directory / "test.err"
    if stderr_file.exists():
        with stderr_file.open("r") as f:
            assert f.read() == expected_stderr
    else:
        assert expected_stderr is None


@pytest.mark.parametrize(
    "jobname, user_command, object, filelog, filelog_stdout, filelog_stderr",
    [
        [
            "myjob",
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_OLD_ARRAY,
            False,
            "/dev/null",
            "/dev/null",
        ],
        [
            "myjob",
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_OLD_ARRAY,
            True,
            "myjob.out",
            "myjob.err",
        ],
        [
            "myjob",
            "./command-by-the-user.sh --with-args ; ./other-command.sh",
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_NEW_ARRAY,
            False,
            "/dev/null",
            "/dev/null",
        ],
        [
            "myjob",
            "./command-by-the-user.sh --with-args ; ./other-command.sh",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_NEW_ARRAY,
            True,
            "myjob.out",
            "myjob.err",
        ],
        [
            "myjob",
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT,
            True,
            "/data/project/test/logs/myjob.log",
            "myjob.err",
        ],
        [
            "myjob",
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT_STDERR,
            True,
            "/dev/null",
            "logs/customlog.err",
        ],
    ],
)
def test_command_array_parsing_from_k8s(
    jobname, user_command, object, filelog, filelog_stdout, filelog_stderr
):
    k8s_metadata = utils.dict_get_object(object, "metadata")
    spec = utils.dict_get_object(object, "spec")
    k8s_command = spec["template"]["spec"]["containers"][0]["command"]

    for command in [
        Command.from_k8s(k8s_metadata=k8s_metadata, k8s_command=k8s_command),
        Command.from_api(
            user_command=user_command,
            filelog=filelog,
            filelog_stdout=filelog_stdout,
            filelog_stderr=filelog_stderr,
            jobname=jobname,
        ),
    ]:
        assert command
        assert command.user_command == user_command
        assert command.filelog == filelog
        assert command.filelog_stdout == filelog_stdout
        assert command.filelog_stderr == filelog_stderr
        array_for_k8s = command.generate_for_k8s()
        assert array_for_k8s[0] == command._WRAPPER[0]
        assert array_for_k8s[1] == command._WRAPPER[1]
        assert array_for_k8s[2] == command._WRAPPER[2]
        assert (
            array_for_k8s[3] == f"exec 1>>{filelog_stdout};exec 2>>{filelog_stderr};{user_command}"
        )
