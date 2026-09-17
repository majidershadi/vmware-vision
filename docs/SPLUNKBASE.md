# Preparing a Splunkbase submission

This repository provides build and inspection steps. Passing local AppInspect does not mean Splunk has certified, approved or listed the app.

1. Run `make release` in the documented build environment. Resolve errors, failures and future failures; review warnings and manual checks in the native reports.
2. Check the two archives and `SHA256SUMS`. Upload the install archives, not a GitHub source ZIP or the development directory.
3. Submit the full app and ingestion TA as separate packages. Their purposes and installation tiers differ.
4. State the supported/tested Splunk versions accurately using [VALIDATION.md](VALIDATION.md). Do not claim a distributed deployment or Splunk Cloud acceptance based only on a standalone test or local inspection.
5. Include the Apache 2.0 license, source repository, build guide, installation guide, support contact and release notes. Retain licenses provided by bundled dependencies.
6. Explain that the app needs existing VMware syslog collection; it creates no enabled network input, index or API polling job. Explain the optional CIM dependency and the `action` migration in 1.1.0.
7. Review the lookup's global sharing, the globally exported derived-field metadata and the source logs with Splunk's reviewer if requested. These support cross-app searches and model membership.
8. Follow the current Splunkbase submission process and any additional validation requested by Splunk. Publish certification or approval claims only after receiving that result.

Keep environment-specific `local/` settings, lab fixtures and build reports outside both install packages. Public synthetic tests remain in the source repository to make parser behavior reproducible.
