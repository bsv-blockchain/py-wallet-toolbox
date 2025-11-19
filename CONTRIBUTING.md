# CONTRIBUTING to BSV Wallet Toolbox (Python)

Thank you for considering contributing to the BSV Blockchain Libraries Project! This document outlines the processes and practices we expect contributors to adhere to.

## Table of Contents

- [General Guidelines](#general-guidelines)
- [Code of Conduct](#code-of-conduct)
  - [Posting Issues and Comments](#posting-issues-and-comments)
  - [Coding and PRs](#coding-and-prs)
- [Getting Started](#getting-started)
- [Pull Request Process](#pull-request-process)
- [Coding Conventions](#coding-conventions)
- [Documentation and Testing](#documentation-and-testing)
- [Compatibility Requirements](#compatibility-requirements)
- [Contact & Support](#contact--support)

## General Guidelines

- **Issues First**: If you're planning to add a new feature or change existing behavior, please open an issue first. This allows us to avoid multiple people working on similar features and provides a place for discussion.
  
- **Stay Updated**: Always pull the latest changes from the main branch before creating a new branch or starting on new code.
  
- **Simplicity Over Complexity**: Your solution should be as simple as possible, given the requirements.

## Code of Conduct

### Posting Issues and Comments

- **Be Respectful**: Everyone is here to help and grow. Avoid any language that might be considered rude or offensive.
  
- **Be Clear and Concise**: Always be clear about what you're suggesting or reporting. If an issue is related to a particular piece of code or a specific error message, include that in your comment.
  
- **Stay On Topic**: Keep the conversation relevant to the issue at hand. If you have a new idea or unrelated question, please open a new issue.

### Coding and PRs

- **Stay Professional**: Avoid including "fun" code, comments, or irrelevant file changes in your commits and pull requests.

## Getting Started

1. **Fork the Repository**: Click on the "Fork" button at the top-right corner of this repository.
  
2. **Clone the Forked Repository**: `git clone https://github.com/YOUR_USERNAME/wallet-toolbox.git`

3. **Navigate to the Directory**: `cd wallet-toolbox/toolbox/py-wallet-toolbox`

4. **Install Dependencies**: `pip install -e .[dev]`

## Pull Request Process

1. **Create a Branch**: For every new feature or bugfix, create a new branch.
  
2. **Commit Your Changes**: Make your changes and commit them. Commit messages should be clear and concise to explain what was done.
  
3. **Run Tests**: Ensure all tests pass: `pytest tests/ -v`.
  
4. **Code Quality**: Ensure code quality checks pass:
   - Format: `black src/ tests/`
   - Lint: `ruff check src/ tests/`
   - Type check: `mypy src/`
  
5. **Documentation**: All code must be fully annotated with English docstrings. Update documentation as needed.
  
6. **Push to Your Fork**: `git push origin your-new-branch`.
  
7. **Open a Pull Request**: Go to your fork on GitHub and click "New Pull Request". Fill out the PR template, explaining your changes.
  
8. **Code Review**: At least two maintainers must review and approve the PR before it's merged. Address any feedback or changes requested.
  
9. **Merge**: Once approved, the PR will be merged into the main branch.

## Coding Conventions

- **Code Style**: We use `black` for formatting (line length: 120) and `ruff` for linting. Run `black src/ tests/` and `ruff check src/ tests/` to ensure your code adheres to this style.
  
- **Type Hints**: All functions must have complete type hints. We use `mypy` in strict mode.
  
- **Testing**: Always include tests for new code or changes. We aim for 90%+ test coverage for implemented methods.
  
- **Documentation**: All functions, classes, and modules should have English docstrings using Google style.

- **No Unnecessary Dependencies**: Minimize external dependencies. Only add dependencies that are essential.

- **Python 3.11+**: All code must be compatible with Python 3.11 and higher.

## Documentation and Testing

- **Documentation**: Update documentation whenever you add or modify code. All public APIs must have comprehensive docstrings.
  
- **Testing**: We use `pytest` for all tests. Write comprehensive tests, ensuring edge cases are covered. 

- **Universal Test Vectors**: When available, all methods must pass official BRC-100 Universal Test Vectors.

- **Test Coverage**: Run `pytest tests/ --cov=src/bsv_wallet_toolbox --cov-report=html` to check coverage. All PRs should maintain or improve current test coverage.

## Compatibility Requirements

**CRITICAL**: This Python implementation must maintain 100% compatibility with TypeScript and Go implementations.

### Cross-Language Compatibility Checklist

- [ ] Same API (method names follow snake_case in Python, but map to camelCase in TypeScript/Go)
- [ ] Same behavior (error handling, edge cases)
- [ ] Universal Test Vectors pass
- [ ] Cross-implementation testing capability

### Reference TypeScript Implementation

When porting features from TypeScript, always include a reference comment:

```python
async def create_action(self, args: CreateActionArgs) -> CreateActionResult:
    """Create action.
    
    Reference: ts-wallet-toolbox/src/Wallet.ts
    """
```

### Database Schema

**DO NOT change database schema without coordination!**

The database schema must be identical across all implementations for Storage Synchronization to work. See `../../doc/08_database_schema.md` for details.

## Contact & Support

If you have any questions or need assistance with your contributions, feel free to reach out. Remember, we're here to help each other grow and improve the BSV Wallet Toolbox.

**Project Owners**: Thomas Giacomo and Darren Kellenschwiler

**Development Team Lead**: Ken Sato @ Yenpoint Inc. & Yosuke Sato @ Yenpoint Inc.

Thank you for being a part of this journey. Your contributions help shape the future of the BSV Blockchain Libraries Project!
