# Contributing to AeroDrift

Thank you for contributing to AeroDrift. Contributions that improve the prototype's clarity, reliability, security analysis, and usefulness for demonstrations are welcome.

## Project Overview

AeroDrift is a Python prototype for **Agentic Cloud Topology & Remediation Graph** analysis. It uses mock AWS resources to build a directed NetworkX graph, detects whether the Internet can reach the Database, generates remediation recommendations, displays results with Rich, and stores scan history in SQLite.

The project intentionally runs without AWS credentials or a cloud account. Keep contributions compatible with this local, deterministic workflow unless a change explicitly introduces an optional integration.

## Local Setup

### Prerequisites

- Python 3.10 or newer
- Git
- No AWS account or credentials

### Installation

Open a terminal in the project directory.

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the application to confirm the local setup:

```bash
python main.py
```

A successful run reports five nodes, four edges, a detected Internet-to-Database path, remediation recommendations, and a saved result in `data/scan_results.db`.

## Coding Standards

- Use Python 3.10+ syntax and standard-library features where practical.
- Follow PEP 8 and use four spaces for indentation.
- Add type hints to new functions and public data structures.
- Add clear docstrings to modules, public functions, and classes.
- Use descriptive names rather than abbreviations.
- Keep modules focused on their existing responsibilities.
- Prefer small, readable functions over duplicated logic.
- Preserve the mock-data-only default and never add credentials or secrets.
- Use parameterized SQL for database writes.
- Keep console output clear and suitable for an internship demonstration.
- Update `README.md` when setup, usage, architecture, or output changes.

Before opening a pull request, run the application and inspect the changed behavior. When tests are added to the project, run the complete test suite as well.

## Commit Message Guidelines

Use short, imperative commit messages that describe one focused change. Keep the first line concise, ideally 50 characters or fewer.

Recommended format:

```text
<type>: <short description>
```

Common types:

- `feat`: Add user-visible functionality
- `fix`: Correct incorrect behavior
- `docs`: Update documentation
- `refactor`: Improve structure without changing behavior
- `test`: Add or update tests
- `chore`: Maintain tooling or project configuration

Examples:

```text
docs: improve architecture guide
refactor: clarify topology construction
fix: handle database write failures
```

Keep unrelated changes in separate commits. Do not commit `.venv/`, Python cache files, local secrets, or generated local database changes unless the contribution specifically requires a database fixture.

## Pull Request Process

1. Create a focused branch from the latest `main` branch.
2. Make the smallest complete change that addresses the issue or proposal.
3. Update documentation when the behavior or setup process changes.
4. Run `python main.py` from the project root.
5. Review the diff for accidental generated files, credentials, or unrelated formatting changes.
6. Push the branch and open a pull request against `main`.
7. Describe the problem, summarize the implementation, and include validation steps.
8. Include sample CLI output or screenshots when changing the dashboard.
9. Respond to review feedback with follow-up commits or a clearly explained discussion.
10. Keep the pull request mergeable and focused on one logical improvement.

A useful pull request description includes:

```markdown
## Summary
- Describe what changed and why.

## Validation
- `python main.py`
- Describe any additional checks performed.

## Screenshots
- Include before-and-after images for visual changes.
```

## Reporting Issues

Before opening an issue, search existing issues and confirm that the problem still occurs on the latest version.

Include the following details:

- A concise, descriptive title
- Operating system and Python version
- Steps to reproduce the problem
- Expected behavior
- Actual behavior and complete error output
- Relevant command output or screenshot
- A minimal example or changed input, when available

Do not include AWS credentials, database secrets, access tokens, or other sensitive information in an issue. Since AeroDrift uses mock data, redact any unrelated local or organizational details from logs before posting them.

## Future Contribution Ideas

Contributions could help AeroDrift grow in several directions:

- Add unit and integration tests for each module.
- Add safe and drifted topology scenarios selectable from the CLI.
- Export graphs as PNG, GraphML, or JSON.
- Add scan-history commands with date and status filters.
- Add structured JSON output for external dashboards.
- Improve validation for resource and relationship schemas.
- Add optional read-only AWS inventory integration behind a separate adapter.
- Add recommendation confidence scores and approval workflows.
- Add continuous integration for formatting, type checking, and tests.
- Improve dashboard accessibility and terminal output for narrow screens.

Please keep proposed enhancements aligned with AeroDrift's educational purpose and its safe-by-default local execution model.
