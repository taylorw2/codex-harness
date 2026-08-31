# Codex Development Harness

A small, practical harness for making AI-assisted software development safer, more predictable, and easier to review.

The basic idea is simple:

> **Don't ask the model to reliably remember what you can deterministically enforce.**

LLMs are very good at reasoning, writing code, and solving problems. But instructions living only in prompts or Markdown files can be forgotten, misinterpreted, or lose influence as context grows.

This project moves important boundaries out of the prompt and into code.

## Philosophy

The model should have room to reason.

The harness defines the boundaries it must operate within.

```text
User
  ↓
AI
  ↓
Tool Request
  ↓
Deterministic Policy
  ↓
Allow / Deny
  ↓
Tool
  ↓
System
```

Instead of telling an agent:

> "Please don't access secrets."

A hook can prevent access to secrets.

Instead of telling an agent:

> "Please keep commits small."

A Git policy can measure the staged diff and reject a commit that exceeds the configured budget.

Prompts still matter. They explain intent, engineering practices, and how the model should recover when a policy rejects an operation.

But deterministic rules should be enforced deterministically.



## Installation

This harness is designed to run from your user-level Codex configuration:

~/.codex/

1. Clone the Repository

Clone the repository somewhere temporary:

```text
git clone https://github.com/taylorw2/codex-harness.git
cd codex-harness
```

2. Inspect the Hooks

Do not install hooks you have not reviewed.

Hooks execute policy code on your machine. Read the configuration and scripts before installing them:

```text
cat hooks.json
cat hooks/protect_secrets.py
cat hooks/git_diff_budget.py
```

Understand what each hook reads, executes, allows, and denies.

That is especially important for a project whose purpose is improving AI development safety.

3. Install Into Codex

Create the hooks directory if necessary:

```text
mkdir -p ~/.codex/hooks
```

Copy the policy scripts:

```text
cp hooks/*.py ~/.codex/hooks/
```

Copy the hook configuration:

```text
cp hooks.json ~/.codex/hooks.json
```

Your Codex directory should now contain:

```text
~/.codex/
├── hooks.json
└── hooks/
    ├── protect_secrets.py
    └── git_diff_budget.py
```

Already Using Codex Hooks?

If you already have:

```text
~/.codex/hooks.json
```

Do not overwrite it blindly.

Review your existing configuration and merge these hooks into it.

The same principle applies to the policy scripts: understand what is already installed before replacing anything.

## Current Policies

### Secret Protection

`hooks/protect_secrets.py`

Runs before tool use and checks requests for potentially sensitive operations or protected resources.

Examples include:

- `.env` files
- API keys and tokens
- SSH credentials
- AWS credentials
- macOS Keychain access
- credential files
- protected Codex configuration
- environment-variable dumping
- suspicious shell execution patterns

Unsafe requests are denied before the tool executes.

### Git Diff Budget

`hooks/git_diff_budget.py`

Measures the staged Git diff before a commit is allowed.

The current policy limits commits by:

- number of changed files
- number of changed lines

The goal is not to prevent the agent from doing substantial work.

The goal is to prevent substantial work from becoming one enormous, difficult-to-review commit.

If a proposed commit exceeds the budget, the model should split the work into smaller, logically coherent commits.

Dependent commits are allowed.

Each commit should leave the repository in a valid state.

## Why the Git Boundary?

The model is allowed to work freely in its local working tree.

It might experiment, refactor, discover a mistake, or temporarily create a large diff.

The important boundary is when that work becomes part of Git history.

For example:

```text
Working tree
900 changed lines

        ↓

Stage logical change #1
220 lines / 4 files

        ↓

Policy check

        ↓

Commit ✓

        ↓

Stage dependent change #2
180 lines / 3 files

        ↓

Policy check

        ↓

Commit ✓
```

The harness constrains the artifact being committed rather than trying to micromanage every step the model takes while solving the problem.

## Repository Structure

```text
.codex/
├── .gitignore
├── README.md
├── hooks.json
└── hooks/
    ├── protect_secrets.py
    └── git_diff_budget.py
```

Only the files needed to share the harness should be committed.

Personal Codex configuration, credentials, runtime state, and other machine-specific files should remain ignored.

## Start Small

This project is intentionally incremental.

A useful harness does not need dozens of policies.

Start with one boundary that matters, test it, understand it, and then add another.

```text
Protect secrets
      ↓
Test it
      ↓
Enforce small commits
      ↓
Test it
      ↓
Add validation policies
      ↓
Test them
      ↓
Repeat when a real problem appears
```

Every policy should exist because it addresses a real failure mode.

## Guidance vs. Enforcement

A useful distinction when building an AI development workflow:

### Guidance

Use prompts and project instructions for things that require judgment.

Examples:

- understand the user's goal
- inspect existing code before editing
- prefer focused changes
- use red-green-refactor
- explain uncertainty
- choose logical commit boundaries

### Enforcement

Use deterministic code for things a program can objectively determine.

Examples:

- Is this request attempting to access a protected secret?
- Does this commit modify more than 5 files?
- Does this commit exceed 300 changed lines?
- Did required tests pass?
- Is a protected file being modified?

If a computer can answer the question reliably, the model shouldn't be responsible for remembering the rule.

## Policy Feedback

A policy rejection should not only say **no**.

It should tell the model why the operation was rejected and give it enough information to recover.

For example:

```text
Git change budget exceeded.

Split the work into smaller, logically coherent commits.
Each commit must leave the repository in a valid state.
Dependent commits are allowed.
```

This creates a useful relationship between deterministic enforcement and model reasoning:

```text
Policy detects the problem
          ↓
Policy rejects the operation
          ↓
Model receives the reason
          ↓
Model reasons about a solution
          ↓
Model tries again
          ↓
Policy verifies it
```

The policy doesn't need to figure out how to split the code.

That's a reasoning problem.

It only needs to enforce the boundary.

## Forking and Customization

This repository is intended to be forked.

Different developers, projects, and organizations have different acceptable boundaries.

Fork it, understand the policies, change the limits, remove rules that don't apply to you, and add deterministic checks for the risks in your own workflow.

A good harness should fit the environment it protects.

## Important

This project is a starting point, not a complete security boundary.

Hooks can reduce risk and enforce useful development constraints, but they do not replace:

- code review
- operating-system permissions
- proper secret management
- sandboxing
- testing
- dependency review
- human judgment

Understand a policy before relying on it.

## Goal

The goal isn't to make AI coding autonomous.

The goal is to let powerful models reason freely **inside boundaries we can actually verify**.
