# Validation scope

The validation environment uses standalone Splunk Enterprise 10.4.1 on Linux and Splunk_SA_CIM 8.7.0. Splunk Enterprise 10.0.2 is a compatibility target; a complete 10.0.2 distributed deployment has not been tested for this release. Do not treat that target as a certification claim.

The parser and CSV lookup use the standard library and support Python 3.9 and 3.13. The package declares both versions and retains a Python 3.9 fallback. Build tools use a separate Python 3.10 or newer virtual environment.

## Completed functional checks

- 55 source tests cover parsing, field contracts, CIM mapping and exclusion rules, dashboard queries, runtime configuration, script sharing and TA packaging.
- A standalone Splunk search in Search & Reporting verified global automatic lookup visibility and tag matching.
- A fixed set of 16 synthetic indexed records produced one Authentication record, eleven Change records and four excluded records. Exclusions included an alarm, a generic failed task, an unknown event and a requested power-on.
- Both custom models returned all sixteen event records with fourteen native action values when scoped to that test set.
- The overview completed its panels against the same records. A separate ephemeral lookup check confirmed failed login mapping and exclusion of logout and a power-on request.

These are functional checks against a small, known data set. They do not measure throughput, prove delivery from a real VMware sender, or validate every Enterprise Security detection. No test records or lab configuration are shipped in either installation package.

## Release checks

Run `make release` to build from source, verify package contents and inspect both archives. The native AppInspect reports accompany the release artifacts. Their warnings and manual checks remain available for review. Local AppInspect is not Splunkbase or Splunk Cloud approval.

## AppInspect review notes

The full app's UCC output produces advisory checks for its SplunkJS bootstrap, bundled dependency code and static `base.html`. The verifier confirms that the template contains no Mako expressions. Data-model warnings are retained; acceleration is disabled by default.

Splunk SDK 2.1.1 is pinned for Python 3.9 compatibility. AppInspect recommends SDK 3.x, whose [published runtime requirement](https://pypi.org/project/splunk-sdk/) is Python 3.13 or newer. Changing that dependency would remove the older-runtime compatibility target. The lookup itself does not use the SDK; the UCC configuration runtime includes it. This warning remains visible for review and is not suppressed.

Other advisory messages concern framework TLS and threading code, dependency metadata examples, Python migration and framework dependency detection. Review the native report for exact locations. The app has no VMware HTTP collector or external API call. Passing the release gate does not remove those review obligations.

## Deployment acceptance still required

Verify the actual raw-data path, timestamps, multiline boundaries, source attribution and sourcetype assignment. Test cross-app search and knowledge bundle replication on every search peer. Compare real VM outcomes with vCenter records, check required CIM fields for the detections you intend to enable, and measure lookup and acceleration cost at your event volume.

For summaries, compare a completed covered interval with raw-backed results. The model counts received records; some audit dashboards deduplicate event identity. Do not use a difference between those totals alone as evidence of a parsing failure.
