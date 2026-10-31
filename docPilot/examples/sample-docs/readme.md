# MicroTest 🧪

A lightweight, zero-dependency testing framework for small applications and microservices. Run your test suites in milliseconds with minimal configuration.

## Features

* **Zero Dependencies:** Keeps your project footprint lightweight.
* **Fast Execution:** Asynchronous parallel test runner.
* **Simple API:** Intuitive `describe`, `test`, and `expect` syntax.
* **Built-in Mocking:** Easily spy on functions and mock network requests.

## Installation

Install the package via your package manager:

```bash
npm install --save-dev microtest
```

## Quick Start

1. Create a test file named `math.test.js`:

```javascript
import { describe, test, expect } from 'microtest';
import { add } from './math.js';

describe('Math Utilities', () => {
  test('should correctly add two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
});
```

2. Run your tests using the CLI:

```bash
npx microtest Run
```

## API Reference

### `describe(name, fn)`
Groups related tests together into a single suite.

### `test(name, fn)`
Defines an individual test case. Aliased as `it()`.

### `expect(value)`
Provides access to validation matchers.

| Matcher | Description |
| :--- | :--- |
| `.toBe(val)` | Strict equality comparison (`===`) |
| `.toEqual(val)` | Deep structural equality for objects/arrays |
| `.toContain(val)` | Checks if an array or string contains a subset |
| `.toThrow(err)` | Validates that a function throws an error |

## Configuration

You can customize the runtime behavior by adding a `microtest.config.json` file to your root directory:

```json
{
  "include": ["src/**/*.test.js"],
  "timeout": 5000,
  "verbose": true
}
```

## License

Distributed under the MIT License. See `LICENSE` for more information.
