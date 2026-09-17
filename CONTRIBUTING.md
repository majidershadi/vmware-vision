# Contributing

Use [BUILD.md](docs/BUILD.md) to create the development environment and run the checks. Edit source under `package/`; UCC output is disposable.

For parser changes, include a small sanitized example and describe the expected fields. Keep event requests separate from successful or failed outcomes. Do not infer a VM, actor, client address or completed state when the source does not provide it. Add a regression check when fixing parsing or field semantics.

For configuration changes, explain the affected tier and whether the change needs a restart or summary rebuild. Update the relevant guide and changelog. Run `make release` before proposing a release, and retain the AppInspect reports for review.

Use short functions and descriptive names. Comments should explain an assumption or a Splunk-specific constraint. Avoid adding dependencies to the parser when the standard library is sufficient.

Do not commit tokens, passwords, private keys, local configuration, real customer logs, installed environments, or generated release packages. Synthetic test fixtures belong in `tests/` and are excluded from install packages.
