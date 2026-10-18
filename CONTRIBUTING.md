# Contributing to NixManager Pro

First off, thank you for considering contributing to **NixManager Pro**! 🎉 It's people like you that make Nix and Linux desktop tooling great.

Follow these guidelines to make contributing as smooth and enjoyable as possible.

---

## Code of Conduct

This project and everyone participating in it is governed by the [NixManager Pro Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [alsghyrblhh@gmail.com](mailto:alsghyrblhh@gmail.com).

---

## How Can I Contribute?

### 1. Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When filing a bug:
* Use the **Bug Report** template.
* Provide clear, step-by-step reproduction instructions.
* Include your OS distribution, Nix version, and terminal/log outputs.
* Attach screenshots or recordings if relevant.

### 2. Suggesting Enhancements

Feature requests are very welcome! When opening a feature request:
* Use the **Feature Request** template.
* Describe the problem you are trying to solve and why existing solutions are insufficient.
* Suggest a concrete workflow or UI mockup if applicable.

### 3. Submitting Code Contributions

1. **Fork the repository** on GitHub.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/<your-username>/NixManagerPro.git
   cd NixManagerPro
   ```
3. **Set up a development environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install pytest pytest-asyncio flake8
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-amazing-feature
   # or
   git checkout -b fix/my-bugfix
   ```
5. **Run the application locally**:
   ```bash
   python3 main.py
   ```
6. **Run the test suite**:
   ```bash
   pytest -v
   ```
7. **Commit your changes** following Conventional Commits (see below).
8. **Push to your fork** and submit a Pull Request.

---

## Commit Message Conventions

We adhere to the [Conventional Commits](https://www.conventionalcommits.org/) specification:

* `feat: ...` for a new feature or user-visible capability.
* `fix: ...` for a bug fix.
* `docs: ...` for documentation changes.
* `style: ...` for formatting or styling without logic changes.
* `refactor: ...` for code reorganization without behavior changes.
* `test: ...` for adding or improving automated tests.
* `chore: ...` for maintenance, CI, build configuration, or dependency bumps.

**Example**:
```git
feat(channels): add single-channel targeted update support

- Add update_single_channel async method to NixChannelManager
- Implement individual refresh buttons per channel row
- Resolves #55
```

---

## Coding Standards

* **Language**: Python 3.10+ using modern type annotations (`typing`, `from __future__ import annotations`).
* **GUI Framework**: `CustomTkinter` and `Tkinter` with clean separation between `core/` (logic & subcommands) and `ui/` (views & widgets).
* **Async & Threading**:
  * Never block the GUI main thread!
  * Long-running subcommands must execute through `AsyncCommandExecutor` or offloaded via `WorkerPool`.
* **Testing**:
  * New core features must include unit tests in the `tests/` directory.
  * Ensure `pytest` passes with 100% success rate before opening a PR.

---

## Pull Request Guidelines

* Link your PR to an existing issue (`Resolves #123` or `Fixes #123`).
* Keep PRs focused on a single logical change; split large refactors into smaller reviews.
* Ensure automated tests and linter checks pass.
* Include before/after screenshots for any UI/UX alterations.

Thank you for helping make Nix accessible and delightful on the desktop! ❄️🚀
