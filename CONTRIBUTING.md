# Contributing to Airtable-to-HSDS API

Thanks for your interest in contributing! This project bridges Airtable data to the [Human Services Data Specification (HSDS)](https://docs.openreferral.org/) API format.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Copy `.env.example` to `.env` and add your Airtable credentials
4. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Run the API: `uvicorn main:app --reload --port 8080`

## How to Contribute

### Bug Reports

Open an issue with:
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS

### Feature Requests

Open an issue describing the feature and its use case.

### Pull Requests

1. Create a feature branch from `main`
2. Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
3. Include docstrings for new functions
4. Test your changes locally
5. Submit a PR with a clear description

## Code Style

- **Python**: PEP 8, type hints where practical
- **TypeScript** (HSDirectory frontend): ESLint defaults
- **Commits**: Use conventional commit messages (e.g., `feat:`, `fix:`, `docs:`)

## Questions?

Open an issue or start a discussion. We're happy to help!
