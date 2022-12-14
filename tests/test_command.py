import pytest

import tests.fake_k8s as fake_k8s
import tjf.utils as utils
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
            fake_k8s.JOB_CONT_NO_EMAILS_NO_FILELOG_NEW_ARRAY,
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
            "./command-by-the-user.sh --with-args",
            fake_k8s.JOB_CONT_NO_EMAILS_YES_FILELOG_NEW_ARRAY,
            True,
            "myjob.out",
            "myjob.err",
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
        Command.from_api(user_command=user_command, filelog=filelog, jobname=jobname),
    ]:
        assert command
        assert command.user_command == user_command
        assert command.filelog == filelog
        assert command.filelog_stdout == filelog_stdout
        assert command.filelog_stderr == filelog_stderr
        array_for_k8s = command.generate_for_k8s()
        assert array_for_k8s[0] == command._WRAPPER_START[0]
        assert array_for_k8s[1] == command._WRAPPER_START[1]
        assert array_for_k8s[2] == f"1>>{filelog_stdout}"
        assert array_for_k8s[3] == f"2>>{filelog_stderr}"
        assert array_for_k8s[4] == command._WRAPPER_END
        assert array_for_k8s[5] == user_command
