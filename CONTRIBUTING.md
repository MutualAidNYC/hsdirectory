# Contributing to Mutual Aid NYC Resource Directory

Thanks for your interest in contributing! This project bridges Airtable data to the [Human Services Data Specification (HSDS)](https://docs.openreferral.org/) API format and presents it via a Next.js directory.

## Getting Started

To run the full stack locally for development:

1. Fork the repository
2. Clone your fork locally (`git clone https://github.com/MutualAidNYC/resource-directory.git`)
3. Copy `.env.example` to `.env` and add your Airtable credentials
4. Start the backend API:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8080
   ```
5. In a second terminal, start the Next.js frontend:
   ```bash
   cd frontend
   npm install
   echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local
   npm run dev
   ```

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
- **TypeScript** (resource-directory frontend): ESLint defaults
- **Commits**: Use conventional commit messages (e.g., `feat:`, `fix:`, `docs:`)

## Questions?

Open an issue or start a discussion. We're happy to help!
