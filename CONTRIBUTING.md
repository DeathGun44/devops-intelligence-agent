# Contributing to DevOps Intelligence Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug already exists in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, AWS region)
   - Relevant logs or screenshots

### Suggesting Features

1. Check if the feature is already requested
2. Create a new issue with:
   - Clear use case
   - Proposed implementation
   - Potential challenges
   - Alternative approaches

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/`
6. Update documentation
7. Commit with clear messages: `git commit -m 'Add amazing feature'`
8. Push to branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/devops-intelligence-agent.git
cd devops-intelligence-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting: `black src/`
- Use pylint for linting: `pylint src/`
- Type hints for all functions
- Docstrings for all classes and functions

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_agent.py
```

## Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for architectural changes
- Add docstrings for all new functions
- Update API documentation

## Commit Messages

Follow conventional commits:
- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `test: Add tests`
- `refactor: Refactor code`
- `chore: Update dependencies`

## Review Process

1. Maintainers will review your PR
2. Address feedback and make requested changes
3. Once approved, PR will be merged

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

