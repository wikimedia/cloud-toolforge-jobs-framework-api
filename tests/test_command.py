import subprocess
from pathlib import Path
from typing import Optional

import pytest

from tjf.command import Command, _remove_filelog_suffix


@pytest.mark.parametrize(
    "name, expected",
    [
        ["some-command 1>>example.out 2>>example.err", "some-command"],
        ["some-command 1>/dev/null 2>/dev/null", "some-command"],
    ],
)
def test_remove_filelog_suffix(name, expected):
    assert _remove_filelog_suffix(name) == expected


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

    cmd = Command.from_api(str(script_path.absolute()), filelog, "test")

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
