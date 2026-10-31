# Changelog

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](https://semver.org).

## - 2026-10-15

### Added
* Parallel worker pooling to handle large execution arrays concurrently.
* Native JSON output reporter using the `--format=json` command-line flag.
* Health status endpoint (`/healthz`) for container orchestrators.

### Changed
* Internal tree-parsing algorithm optimized, reducing startup memory signatures by 22%.
* Standard output logs modified to follow structured JSON formats for easier parsing.

### Fixed
* Addressed an unhandled exception when evaluating empty or zero-byte configuration matrices.
* Fixed a memory leak in asynchronous processing hooks when timeouts were reached.

## - 2026-04-01

### Added
* Core engine engine release featuring basic structural validation parsing.
* Standard matchers ecosystem: equality check, object parsing, and error-catching hooks.
* Initial configuration engine loading via a root JSON file pattern.
