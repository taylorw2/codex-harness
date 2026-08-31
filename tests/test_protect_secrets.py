# tests/test_protect_secrets.py

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))

import protect_secrets


def test_blocks_real_home_codex_config():
    home = os.path.expanduser("~")

    assert protect_secrets.contains_protected_resource(
        {"command": f"cat {home}/.codex/config.toml"}
    )


def test_blocks_real_home_hooks_json():
    home = os.path.expanduser("~")

    assert protect_secrets.contains_protected_resource(
        {"command": f"cat {home}/.codex/hooks.json"}
    )


def test_blocks_real_home_secret_hook():
    home = os.path.expanduser("~")

    assert protect_secrets.contains_protected_resource(
        {"command": f"cat {home}/.codex/hooks/protect_secrets.py"}
    )


def test_blocks_env_file():
    assert protect_secrets.contains_protected_resource(
        {"command": "cat .env"}
    )


def test_blocks_ssh_key():
    assert protect_secrets.contains_protected_resource(
        {"command": "cat ~/.ssh/id_rsa"}
    )


def test_blocks_secret_environment_variable():
    assert protect_secrets.contains_protected_resource(
        {"command": "echo $OPENAI_API_KEY"}
    )


def test_allows_normal_file():
    assert not protect_secrets.contains_protected_resource(
        {"command": "cat README.md"}
    )


def test_blocks_environment_dump():
    allowed, reason = protect_secrets.check_bash(
        {"command": "env"}
    )

    assert allowed is False
    assert reason is not None


def test_blocks_nested_shell():
    allowed, reason = protect_secrets.check_bash(
        {"command": "bash -c 'echo hello'"}
    )

    assert allowed is False
    assert reason is not None


def test_allows_safe_shell_command():
    allowed, reason = protect_secrets.check_bash(
        {"command": "git status"}
    )

    assert allowed is True
    assert reason is None

def test_blocks_dotenv_variants():
    blocked = [
        ".env",
        ".env.local",
        ".env.production",
        "/project/.env",
        "/project/.env.test",
    ]

    for path in blocked:
        assert protect_secrets.contains_protected_resource(
            {"command": f"cat {path}"}
        ), f"Policy allowed protected path: {path}"

def test_blocks_secret_variable_variants():
    blocked = [
        "$OPENAI_API_KEY",
        "$ANTHROPIC_API_KEY",
        "$AWS_SECRET_ACCESS_KEY",
        "$GITHUB_TOKEN",
        "$DATABASE_URL",
    ]

    for variable in blocked:
        assert protect_secrets.contains_protected_resource(
            {"command": f"echo {variable}"}
        ), f"Policy allowed secret variable: {variable}"

def test_allows_normal_development_commands():
    allowed_commands = [
        "git status",
        "git diff",
        "python3 -m pytest -q",
        "cat README.md",
        "ls hooks",
        "git log --oneline",
    ]

    for command in allowed_commands:
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }

        allowed, reason = protect_secrets.check(payload)

        assert allowed is True, (
            f"Safe command unexpectedly blocked: {command}. "
            f"Reason: {reason}"
        )
