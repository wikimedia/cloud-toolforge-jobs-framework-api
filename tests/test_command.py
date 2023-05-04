import subprocess
from pathlib import Path

import pytest

import tests.fake_k8s as fake_k8s
import tjf.utils as utils
from tjf.command import Command


def test_generate_command_no_filelog(tmp_path_factory):
    # this is provided by a pytest fixture, https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html
    directory = tmp_path_factory.mktemp("testcmd")

    script_path = Path(__file__).parent / "helpers" / "gen-output" / "both.sh"

    cmd = Command.from_api(
        user_command=str(script_path.absolute()),
        filelog=False,
        filelog_stdout=None,
        filelog_stderr=None,
        jobname="test",
    )

    result = subprocess.run(cmd.generate_for_k8s(), capture_output=True, text=True, cwd=directory)

    assert result.stdout == "this text has no meaningful content,\n"
    assert result.stderr == "it is just an example\n"

    assert not any(directory.glob("*"))


def test_generate_command_filelog(tmp_path_factory):
    # this is provided by a pytest fixture, https://docs.pytest.org/en/7.1.x/how-to/tmp_path.html
    directory = tmp_path_factory.mktemp("testcmd")

    script_path = Path(__file__).parent / "helpers" / "gen-output" / "both.sh"

    cmd = Command.from_api(
        user_command=str(script_path.absolute()),
        filelog=True,
        filelog_stdout="test.out",
        filelog_stderr="test.err",
        jobname="test",
    )

    result = subprocess.run(cmd.generate_for_k8s(), capture_output=True, text=True, cwd=directory)

    assert result.stdout == ""
    assert result.stderr == ""

    stdout_file = directory / "test.out"
    assert stdout_file.exists()
    assert stdout_file.read_text() == "this text has no meaningful content,\n"

    stderr_file = directory / "test.err"
    assert stderr_file.exists()
    assert stderr_file.read_text() == "it is just an example\n"


@pytest.mark.parametrize(
    "user_command, object, filelog, filelog_stdout, filelog_stderr",
    [
        [
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_OLD_ARRAY,
            False,
            "/dev/null",
            "/dev/null",
        ],
        [
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_OLD_ARRAY,
            True,
            "myjob.out",
            "myjob.err",
        ],
        [
            "./command-by-the-user.sh --with-args ; ./other-command.sh",
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_NEW_ARRAY,
            False,
            "/dev/null",
            "/dev/null",
        ],
        [
            "./command-by-the-user.sh --with-args ; ./other-command.sh",
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_V2_ARRAY,
            False,
            None,
            None,
        ],
        [
            "./command-by-the-user.sh --with-args ; ./other-command.sh",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_NEW_ARRAY,
            True,
            "myjob.out",
            "myjob.err",
        ],
        [
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT,
            True,
            "/data/project/test/logs/myjob.log",
            "myjob.err",
        ],
        [
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_CUSTOM_STDOUT_STDERR,
            True,
            "/dev/null",
            "logs/customlog.err",
        ],
    ],
)
def test_command_array_parsing_from_k8s(
    user_command, object, filelog, filelog_stdout, filelog_stderr
):
    k8s_metadata = utils.dict_get_object(object, "metadata")
    spec = utils.dict_get_object(object, "spec")
    k8s_command = spec["template"]["spec"]["containers"][0]["command"]

    command = Command.from_k8s(k8s_metadata=k8s_metadata, k8s_command=k8s_command)

    assert command
    assert command.user_command == user_command
    assert command.filelog == filelog
    assert command.filelog_stdout == filelog_stdout
    assert command.filelog_stderr == filelog_stderr
