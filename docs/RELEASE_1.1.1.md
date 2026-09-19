# VMware Vision 1.1.1 and ingestion TA 1.0.2

This maintenance release fixes missing normalization fields on syslog records with leading or trailing whitespace. It also improves classification of the supplied ESXi and vCenter message shapes. The full app changes to 1.1.1; the ingestion TA remains 1.0.2 with exactly the same archive bytes.

## Post-release findings

Additional production samples exposed unresolved VM-name extraction, diagnostic event-type false positives and fragmented reconfiguration parsing. See the [current README](https://github.com/majidershadi/vmware-vision#known-111-audit-limitations) for details. The published 1.1.1 archives remain unchanged; this advisory does not claim those issues are fixed.

## Fixes

- **CSV lookup matching:** quote the `_raw`, `host` and `sourcetype` input keys so boundary whitespace survives the external lookup round trip. Original raw text is preserved. Empty normalized outputs remain unquoted so existing missing-field checks and `coalesce` searches keep their behavior.
- **Hostd logout:** recognize explicit `Vimsvc.ha-eventmgr` logout records with numeric event IDs. Preserve the actor, source address and event time when supplied. Logout remains outside the scoped CIM Authentication mapping.
- **Service diagnostics:** recognize supported Envoy HTTP access records, UI subscription retry messages and SPS diagnostic fragments. An HTTP success code is not treated as proof that a VM operation completed.
- **Audit candidates:** include numeric Hostd event records in the audit search filter.
- **Coverage:** keep absent normalization results visible as `lookup_missing`, separate from `unclassified` messages that the parser processed but did not recognize.

Unknown events are not turned into successful changes, and missing VM identities are not invented.

## Packages and installation tiers

| Archive | Version | Placement |
|---|---|---|
| `vmware_vision-1.1.1.tar.gz` | 1.1.1 | Search heads or standalone Splunk |
| `TA-vmware-vision-1.0.2.tar.gz` | 1.0.2, unchanged | First full parsing tier: HF or indexers |

The TA has no Python lookup, CIM mapping, dashboards or enabled inputs. The search app supplies normalization and distributes its search-time knowledge to peers. Do not install another TA on the standalone lab just to apply this lookup fix. See [TA configuration](TA_CONFIGURATION.md) and [deployment](DEPLOYMENT.md).

Both archives, checksums, native AppInspect reports and verification evidence are attached to the [GitHub release](https://github.com/majidershadi/vmware-vision/releases/tag/v1.1.1). Install the package archive, not GitHub's source ZIP.

## Upgrade

1. Back up the existing app, including `local/` and `metadata/local.meta`. Record index macros and enabled acceleration settings.
2. Verify the downloaded archive with the release's `SHA256SUMS.txt`.
3. Upgrade the full app through the normal search-tier deployment path. Use the search head cluster deployer for an SHC. Preserve intended local settings and review overrides of props, transforms, fields, metadata and models.
4. Restart when required by that deployment path and start a new search. Confirm `parser_version=1.1.1` in VMware Vision and Search & Reporting, and check every distributed search peer.
5. Recheck the original records that returned missing parser fields. Inspect remaining missing rows separately from unsupported message shapes.
6. Rebuild affected VMware or CIM acceleration summaries during a suitable maintenance window if historical summaries must reflect corrected parsing. Search-time changes do not require reindexing.

Upgrading from 1.0.x also requires replacing custom native `action` filters with `vmware_action`. Eligible CIM events use standardized `action` values. The bundled dashboards already use this contract. See [installation](INSTALLATION.md), [data models](DATA_MODELS.md) and [CIM/ES integration](CIM.md).

## Validation and limits

- 60 source tests passed in the build environment and Splunk's Python 3.9 and 3.13 runtimes.
- Thirteen supported live lookup cases passed in both VMware Vision and Search & Reporting, including spaces, tabs, CSV quotes, commas, Unicode and embedded LF. Original raw text was preserved.
- Existing lab fixtures produced one CIM Authentication record, eleven Change records and four exclusions. Failed login, logout exclusion and requested-operation exclusion were checked separately.
- Native Linux AppInspect reports no errors, failures or future failures. The full app retains ten advisory warnings; the unchanged TA report has none. Reports remain available for review.
- Functional validation uses standalone Splunk Enterprise 10.4.1 and CIM 8.7.0. Distributed Splunk 10.0.2 remains a compatibility target, not a completed deployment acceptance test. Real-sender coverage, peer replication, volume and ES detection requirements need validation in the target environment.

**Known limitation:** a synthetic event with embedded CRLF still fails to match in the tested external lookup path. CRLF was an additional edge-case test, not an application requirement or a change to VMware/Splunk collection. The reported production issue was trailing whitespace. Do not change event boundaries or reindex to hide this separate limitation. See [troubleshooting](TROUBLESHOOTING.md).

This remains a beta release while the documented deployment and compatibility limits apply. GitHub prerelease status is independent of Splunkbase review. Local AppInspect does not constitute Splunkbase or Splunk Cloud approval; the publisher handles Splunkbase submission separately.

No VMware API polling is included. The app uses existing syslog data. API collection may be considered for a future version.

## Rollback and support

Restore the previous full app and backed-up local settings through the same deployment mechanism. Rebuild affected summaries if their fields or mappings changed. Do not delete indexes. TA 1.0.2 does not need rollback for this app-only fix.

For an issue, include the app/Splunk versions, affected sourcetype and peer, a sanitized raw record, the expected result and relevant search-log errors. Never include credentials or unsanitized production data. Use [GitHub Issues](https://github.com/majidershadi/vmware-vision/issues).
