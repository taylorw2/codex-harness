# tests/test_pre_tool_policy.py

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))

import pre_tool_policy


def bash_payload(command):
    return {
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
        },
        "cwd": "/tmp",
    }


def test_detects_git_commit():
    assert pre_tool_policy.is_git_commit(
        bash_payload('git commit -m "test"')
    )


def test_detects_absolute_git_commit():
    assert pre_tool_policy.is_git_commit(
        bash_payload('/usr/bin/git commit -m "test"')
    )


def test_does_not_treat_git_status_as_commit():
    assert not pre_tool_policy.is_git_commit(
        bash_payload("git status")
    )


def test_non_bash_tool_is_not_git_commit():
    payload = {
        "tool_name": "apply_patch",
        "tool_input": {"patch": "whatever"},
    }

    assert not pre_tool_policy.is_git_commit(payload)


def test_security_runs_before_git_budget():
    payload = bash_payload('git commit -m "test"')

    with (
        patch.object(
            pre_tool_policy.protect_secrets,
            "check",
            return_value=(False, "secret blocked"),
        ) as security,
        patch.object(
            pre_tool_policy.git_diff_budget,
            "check",
            return_value=(True, None),
        ) as diff_budget,
    ):
        allowed, reason = pre_tool_policy.inspect_request(payload)

    assert allowed is False
    assert reason == "secret blocked"

    security.assert_called_once()
    diff_budget.assert_not_called()


def test_git_budget_runs_for_commit():
    payload = bash_payload('git commit -m "test"')

    with (
        patch.object(
            pre_tool_policy.protect_secrets,
            "check",
            return_value=(True, None),
        ),
        patch.object(
            pre_tool_policy.git_diff_budget,
            "check",
            return_value=(False, "too large"),
        ) as diff_budget,
    ):
        allowed, reason = pre_tool_policy.inspect_request(payload)

    assert allowed is False
    assert reason == "too large"
    diff_budget.assert_called_once_with(payload)


def test_git_budget_does_not_run_for_regular_command():
    payload = bash_payload("git status")

    with (
        patch.object(
            pre_tool_policy.protect_secrets,
            "check",
            return_value=(True, None),
        ),
        patch.object(
            pre_tool_policy.git_diff_budget,
            "check",
        ) as diff_budget,
    ):
        allowed, reason = pre_tool_policy.inspect_request(payload)

    assert allowed is True
    assert reason is None

    diff_budget.assert_not_called()
