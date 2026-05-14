# Contributing to Desksor

Thank you for your interest in contributing to Desksor! This document explains how to get started.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/desksor.git
   cd desksor
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install in editable mode with dev dependencies**
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```

## Running Tests

Tests require Windows and at least Notepad and Calculator to be available (they are on every Windows install).

```bash
python -m pytest tests/ -v
```

## Code Standards

- **All methods must return** `{"success": bool, "data": any, "error": str, "time_ms": int}`
- **Never raise unhandled exceptions** — catch everything and return `success: false`
- **Error messages must be helpful** — tell the user what IS available when something is NOT found
- **Every action is logged** to `desksor.log` with `[timestamp] [app] [action] [element] [success] [time_ms]`
- **Windows only** — pywinauto is Windows only. Do not add Mac/Linux code paths
- **No external services** — no API calls, no analytics, no telemetry without explicit user opt-in

## What NOT to add

This repo is the free, local, open-source version. Please do not add:

- Cloud functionality
- User authentication or accounts
- Billing or payment logic
- Dashboard or web UI
- Mac or Linux support
- External API calls
- Databases

These are planned paid features.

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Write tests for your changes
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Keep PRs focused — one feature or fix per PR
5. Update documentation if you add new methods

## Reporting Issues

Please include:
- Windows version
- Python version
- App you were trying to control
- Full error output or log from `desksor.log`
- Steps to reproduce

## License

By contributing, you agree your contributions will be licensed under the MIT License.
