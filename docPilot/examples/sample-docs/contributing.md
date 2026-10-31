# Contributing to MicroTest

Thank you for considering contributing! We want to keep this testing framework small, fast, and accessible.

## Development Setup

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com
   ```
3. **Install development dependencies**:
   ```bash
   npm install
   ```

## Workflow

* **Branching:** Create a feature branch off `main` (e.g., `feat/add-json-reporter` or `fix/timeout-leak`).
* **Testing:** Ensure all existing tests pass before writing new code:
   ```bash
   npm test
   ```
* **Documentation:** If you add a new feature or matcher, update the `README.md` tables accordingly.

## Pull Request Guidelines

1. Link your Pull Request to an open issue if applicable.
2. Keep your changes focused. If you want to fix multiple unrelated issues, open separate PRs.
3. Verify that your code adheres to the project's formatting standard (`npm run lint`).
