# Contributing to Food Processing System

First off — thank you for taking the time to contribute! 🎉

This document explains how to set up your environment, the standards we follow,
and how to submit changes.

## Code of Conduct

This project and everyone participating in it is governed by our
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold it.

## Getting Started

```bash
# Fork & clone, then:
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/short-description
   ```
2. **Make your change** with clear, focused commits.
3. **Add or update tests** for any behaviour change.
4. **Run the quality gates** locally (all must pass):
   ```bash
   pytest             # tests
   ruff check .       # lint
   ruff format --check .   # formatting
   mypy               # type checking
   ```
5. **Open a Pull Request** using the PR template and link any related issue.

## Coding Standards

- **Python 3.10+**, with **type hints** on public functions.
- Follow the existing **layered architecture**: `cli → services → repositories → database`.
- **Never** build SQL with string concatenation — always pass parameters.
- **Never** commit secrets. Use environment variables / `.env` (which is git-ignored).
- Keep functions small and add docstrings to public APIs.
- Lint and format with **ruff** (config lives in `pyproject.toml`).

## Commit Messages

Use clear, imperative messages, ideally following
[Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add CSV export for orders
fix: re-prompt on invalid integer input
docs: clarify MySQL setup
```

## Reporting Bugs & Requesting Features

Please use the issue templates:

- 🐛 [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)

## Questions?

Open a [discussion or issue](https://github.com/aashishbharti04/food-processing-system/issues),
or reach out at **aashish@marketdoctorsonline.com**.
