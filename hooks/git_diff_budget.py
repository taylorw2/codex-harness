#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Change budget
#
# First version: hard-coded globally.
# We can make this repo-configurable later.
# ---------------------------------------------------------------------------

MAX_CHANGED_FILES = 5
MAX_CHANGED_LINES = 300


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_git(
    cwd: str,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """
    Run a Git command without invoking a shell.

    shell=False is intentional. Policy code should not execute
    arbitrary shell input.
    """
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repository(cwd: str) -> bool:
    """Return True when cwd is inside a Git working tree."""
    result = run_git(
        cwd,
        "rev-parse",
        "--is-inside-work-tree",
    )

    return (
        result.returncode == 0
        and result.stdout.strip() == "true"
    )


# ---------------------------------------------------------------------------
# Diff inspection
# ---------------------------------------------------------------------------

def get_staged_diff_stats(
    cwd: str,
) -> tuple[int, int]:
    """
    Return:

        (changed_files, changed_lines)

    for the staged changes that would enter the next commit.

    Changed lines are:

        additions + deletions

    Binary files count toward changed_files but contribute zero lines.
    """
    result = run_git(
        cwd,
        "diff",
        "--cached",
        "--numstat",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Unable to inspect staged Git diff: "
            + result.stderr.strip()
        )

    changed_files = 0
    changed_lines = 0

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        parts = line.split("\t", 2)

        if len(parts) != 3:
            raise RuntimeError(
                f"Unexpected git diff --numstat output: {line!r}"
            )

        additions, deletions, _path = parts

        changed_files += 1

        # Git reports binary changes as:
        #
        # -    -    path/to/file
        #
        # Count the file but not binary "lines".
        if additions == "-" or deletions == "-":
            continue

        try:
            changed_lines += int(additions)
            changed_lines += int(deletions)
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid Git numstat output: {line!r}"
            ) from exc

    return changed_files, changed_lines


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

def check(
    payload: dict[str, Any],
) -> tuple[bool, str | None]:
    """
    Check whether the staged Git change is within the allowed budget.

    This function assumes the caller has already determined that the
    proposed operation is a Git commit.

    Security should be checked BEFORE calling this policy.
    """
    cwd = payload.get("cwd", "")

    if not isinstance(cwd, str) or not cwd:
        return False, "Git diff budget could not determine the working directory."

    path = Path(cwd)

    if not path.is_dir():
        return False, f"Git working directory does not exist: {cwd}"

    if not is_git_repository(cwd):
        return False, "Git commit requested outside a Git repository."

    try:
        changed_files, changed_lines = get_staged_diff_stats(cwd)
    except Exception as exc:
        # Policy inspection failed, so fail closed.
        return (
            False,
            f"Git diff budget could not safely inspect the staged change: {exc}",
        )

    # ------------------------------------------------------------------
    # FILE BUDGET
    # ------------------------------------------------------------------

    if changed_files > MAX_CHANGED_FILES:
        return (
            False,
            "Git change budget exceeded: "
            f"{changed_files} staged files exceeds the "
            f"maximum of {MAX_CHANGED_FILES}. "
            "Split the work into smaller, logically coherent commits. "
            "Each commit must leave the repository in a valid state. "
            "Dependent commits are allowed.",
        )

    # ------------------------------------------------------------------
    # LINE BUDGET
    # ------------------------------------------------------------------

    if changed_lines > MAX_CHANGED_LINES:
        return (
            False,
            "Git change budget exceeded: "
            f"{changed_lines} staged changed lines exceeds the "
            f"maximum of {MAX_CHANGED_LINES}. "
            "Split the work into smaller, logically coherent commits. "
            "Each commit must leave the repository in a valid state. "
            "Dependent commits are allowed.",
        )

    return True, None
