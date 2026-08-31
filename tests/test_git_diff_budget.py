# tests/test_git_diff_budget.py

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))

import git_diff_budget


class FakeResult:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_counts_staged_files_and_lines():
    result = FakeResult(
        stdout=(
            "10\t5\tfile1.py\n"
            "20\t10\tfile2.py\n"
        )
    )

    with patch.object(git_diff_budget, "run_git", return_value=result):
        files, lines = git_diff_budget.get_staged_diff_stats("/tmp")

    assert files == 2
    assert lines == 45


def test_binary_file_counts_as_file_but_not_lines():
    result = FakeResult(
        stdout=(
            "-\t-\timage.png\n"
            "5\t2\tcode.py\n"
        )
    )

    with patch.object(git_diff_budget, "run_git", return_value=result):
        files, lines = git_diff_budget.get_staged_diff_stats("/tmp")

    assert files == 2
    assert lines == 7


def test_rejects_too_many_files(tmp_path):
    payload = {"cwd": str(tmp_path)}

    with (
        patch.object(git_diff_budget, "is_git_repository", return_value=True),
        patch.object(
            git_diff_budget,
            "get_staged_diff_stats",
            return_value=(git_diff_budget.MAX_CHANGED_FILES + 1, 10),
        ),
    ):
        allowed, reason = git_diff_budget.check(payload)

    assert allowed is False
    assert "files" in reason.lower()


def test_rejects_too_many_lines(tmp_path):
    payload = {"cwd": str(tmp_path)}

    with (
        patch.object(git_diff_budget, "is_git_repository", return_value=True),
        patch.object(
            git_diff_budget,
            "get_staged_diff_stats",
            return_value=(1, git_diff_budget.MAX_CHANGED_LINES + 1),
        ),
    ):
        allowed, reason = git_diff_budget.check(payload)

    assert allowed is False
    assert "lines" in reason.lower()


def test_allows_change_within_budget(tmp_path):
    payload = {"cwd": str(tmp_path)}

    with (
        patch.object(git_diff_budget, "is_git_repository", return_value=True),
        patch.object(
            git_diff_budget,
            "get_staged_diff_stats",
            return_value=(2, 100),
        ),
    ):
        allowed, reason = git_diff_budget.check(payload)

    assert allowed is True
    assert reason is None


def test_fails_closed_when_diff_inspection_fails(tmp_path):
    payload = {"cwd": str(tmp_path)}

    with (
        patch.object(git_diff_budget, "is_git_repository", return_value=True),
        patch.object(
            git_diff_budget,
            "get_staged_diff_stats",
            side_effect=RuntimeError("boom"),
        ),
    ):
        allowed, reason = git_diff_budget.check(payload)

    assert allowed is False
    assert "could not safely inspect" in reason.lower()
