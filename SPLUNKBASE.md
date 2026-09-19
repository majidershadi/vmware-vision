# Splunkbase publishing guide

Copy the text below into two separate listings. The Summary, Details, Installation, Troubleshooting, Contact and Version History sections follow the public Splunkbase listing layout. Submission-form labels may differ slightly. Splunkbase submission and acceptance of its terms are handled by the publisher.

## 1. Listing fields

| Field | VMware Vision app | VMware Vision technical add-on |
|---|---|---|
| Display name | VMware Vision for Splunk | VMware Vision Ingestion Add-on |
| Package / app ID | `vmware_vision` | `TA-vmware-vision` |
| Type | App | Add-on |
| Version | 1.1.1 | 1.0.2 |
| Upload file | `vmware_vision-1.1.1.tar.gz` | `TA-vmware-vision-1.0.2.tar.gz` |
| Author / publisher | Your existing Splunkbase publisher account; project author: Majid Ershadi | Same account |
| Primary category | IT Operations | IT Operations |
| Additional category, if offered | Security, Fraud & Compliance | Leave unset unless a more suitable ingestion category is available |
| Product | Splunk Enterprise | Splunk Enterprise |
| Platform-version selection supported by completed testing | 10.4; the tested patch is 10.4.1 | 10.4 for configuration/package validation; first-parser deployment must still be checked in the target topology |
| Operating system | Linux | Linux |
| License | Apache License 2.0 | Apache License 2.0 |
| Price | Free | Free |
| Support model | Developer support through GitHub Issues; no paid SLA | Same |
| CIM | Scoped Authentication and Change mappings; tested with Splunk_SA_CIM 8.7.0 | No direct CIM mapping; the search app supplies it |
| Python | 3.9 and 3.13 | No Python runtime dependency |
| Installation tier | Search head or standalone Splunk | First full parsing tier: HF or indexers |
| Dependencies | Existing VMware syslog collection; CIM only when using CIM models | Existing collection/input/forwarding configuration; full app for search-time fields and dashboards |
| Suggested tags | VMware, vCenter, ESXi, Aria, syslog, VM audit, CIM, virtualization | VMware, syslog, parsing, heavy forwarder, indexer, technical add-on |

Select only platform versions you are prepared to support. Splunk 10.0.2 is a compatibility target, not a completed distributed acceptance test for this release. Do not select every 10.x version merely because the Python syntax works. Do not claim Splunk Cloud approval or universal Enterprise Security compatibility. The app manifest currently identifies development status as Beta; preserve that qualification wherever the form asks for maturity.

If the form asks for a publisher email, use the public support email you maintain in your Splunkbase profile. The support URL below is ready to use; no new support address is required by this project.

## 2. VMware Vision app: short description

Review VMware VM creation, changes, power operations, migrations and failures from syslog, with audit dashboards and scoped CIM Authentication and Change mappings.

## 3. VMware Vision app: Summary

VMware Vision turns existing vCenter, ESXi and Aria syslog into a record of VM activity. Investigate creation, removal, power operations, configuration changes, migrations, snapshots, users and failures from one app.

The app includes VM history and change-audit dashboards, source coverage checks, a detailed VMware data model and a compact model for optional accelerated activity trends. Selected explicit event outcomes map into CIM Authentication and Change.

VMware Vision uses logs you already collect. Version 1.1.1 does not poll VMware APIs, maintain complete live inventory or change VMware configuration. API collection may be considered for a future release; it is not included in this version.

## 4. VMware Vision app: Details

### Features

- VMware Overview: activity counts, recent VM events, users and failures.
- VM History: recorded operations and the last successfully observed state within the selected history.
- Configuration and Change Audit: recorded reconfiguration, rename, migration and snapshot activity, with supplied change details.
- Operations and Security: authentication, permission, alarm, host and task context.
- Setup and Coverage: source freshness, parser status, event classification and identity quality.
- Accelerated Activity: optional aggregate trends from the compact VMware Vision Activity model.
- Automatic search-time normalization, including searches run outside the app.
- Scoped CIM Authentication and Change mappings with the native operation retained in `vmware_action`.

### Data sources and identity

Supported sourcetypes are `vmware:vision:vcenter`, `vmware:vision:esxi`, `vmware:vision:aria` and `vmware:vision:json`. vCenter event records are the primary source for VM lifecycle and configuration auditing. ESXi adds host and local operational context. Aria can relay VMware records; its own appliance diagnostics do not replace vCenter event history.

Identity prefers a VM UUID or a vCenter-scoped managed object ID. Names alone are weaker identifiers because they can change or be reused. The parser does not invent a VM identity, actor, client address or before/after value when the event does not supply it.

### Event outcomes and CIM

Requests are kept separate from completed outcomes. A starting operation does not establish that a VM powered on, and a failed operation does not update its successful observed state.

Eligible login outcomes map into Authentication. Selected VM lifecycle, power, configuration, migration and snapshot outcomes map into Change. Requested operations, logout, generic tasks and service diagnostics are excluded from these initial CIM mappings. Alarm, permission, host and datastore events remain searchable in the app but are outside this initial CIM scope.

Native operation names use `vmware_action`; eligible CIM records use CIM values in `action`. For example, a successful power-on has `vmware_action=power_on`, `action=started` and `status=success`.

### Performance and limits

Acceleration is disabled by default. The compact model is intended for counts and trends, not detailed VM history. Summary-only searches omit unsummarized data. Model totals count received records and may include duplicates, while some audit panels deduplicate event identity.

The automatic lookup uses search-time Python. Search cost depends on scope and volume; use explicit indexes, narrow time windows and measured acceleration settings. Some exported derived-field metadata affects shared fields such as `action` and `status`, so validate search cost alongside other installed content.

No enabled input, index definition, forwarding destination, API polling job or scheduled alert is installed. The app does not send VMware events to an external service. VMware product-version coverage depends on the actual forwarded format; this release does not claim a complete vSphere/Aria version matrix.

VMware Vision is an independent project and is not an official VMware, Broadcom or Splunk product.

## 5. VMware Vision app: Installation

1. Download `vmware_vision-1.1.1.tar.gz` from the GitHub release and verify its checksum against `SHA256SUMS.txt`. Do not install the GitHub source ZIP as a Splunk app.
2. Back up an existing app's local configuration before upgrading. On an independent search head or standalone instance, install through Apps → Manage Apps → Install app from file. Use the search head cluster deployer for an SHC.
3. Install the ingestion TA on the first full parsing tier in a distributed raw-syslog path. A standalone instance with the full app already has these parsing settings.
4. Create or select the destination index on the indexing tier. Configure VMware forwarding, collection and sourcetypes through your existing collection configuration. Neither package enables collection for you.
5. Open Settings → Advanced search → Search macros, select VMware Vision and edit `vmware_vision_indexes`. Use a definition such as `(index=vmware OR index=vmware_syslog)`. Ensure search roles can access those indexes.
6. Check known records over a short time window. Confirm timestamps, original source, event classification, VM identity and outcome against the raw messages.
7. Check a VMware search in Search & Reporting to confirm that the automatic lookup is visible outside the app. On distributed systems, verify every search peer receives the complete knowledge bundle.
8. Test custom model membership before enabling acceleration. The custom models use the VMware index macro and do not require Splunk_SA_CIM.
9. For CIM, install the version supported by your Splunk/ES deployment on the search tier. Add the VMware indexes to `cim_Authentication_indexes` and `cim_Change_indexes`, preserving existing source indexes. Verify tags and model membership before enabling or rebuilding summaries.
10. For Accelerated Activity, enable the separate `VMware_Vision_Activity` model, choose a suitable summary range, wait for coverage and click Submit on the dashboard.

Validation search:

```spl
index=vmware sourcetype=vmware:vision:*
| stats count by parser_version parser_status record_kind
```

Custom model check:

```spl
| datamodel VMware_Vision Events flat strict_fields=false
| table _time vcenter vm_name event_type vmware_action status
| head 30
```

The installation guide contains file-based alternatives, index examples and a complete upgrade/rollback procedure:

https://github.com/majidershadi/vmware-vision/blob/main/docs/INSTALLATION.md

## 6. VMware Vision app: Troubleshooting

| Symptom | What to check |
|---|---|
| Upload rejects check_for_updates | Upload the corrected archive. Its `[package]` setting must be `check_for_updates = true`; UCC `meta.checkForUpdates` must also remain true when rebuilding. Editing only an installed copy does not change the upload archive. |
| No events or empty dashboards | Check collection first, then the time window, index macro, role index access and exact sourcetype. |
| Most events are diagnostics or unknown actions | Inspect actual event classes. Service logs such as routine API calls or activation checks are not necessarily VM operations. |
| VM name, user or change details are missing | Compare with the original event. The parser leaves unavailable or ambiguous fields empty. |
| Search is waiting for input | Click Submit. Check unresolved tokens and the shared dashboard base search. A post-process `stats` query is not a standalone data search. |
| Accelerated Activity is empty | Check the custom Activity model, index scope, summary coverage and time range. CIM acceleration does not enable this separate model. |
| CIM models are empty | Check the two CIM index macros, tags, permissions, event eligibility and exported derived-field definitions. |
| Lookup works only inside VMware Vision | Check props/transform/script sharing, local metadata overrides and search-bundle exclusions. The script, parser and CIM module must all be present. |
| A field appears in a table but a filter returns no events | Check the app's `INDEXED_VALUE=false` definitions for computed fields and any local overrides. |
| Totals differ between audit and accelerated views | Compare the same covered window and account for repeated delivery and audit deduplication. |
| Behavior changed after upgrade | Review local props, transforms, fields, metadata, models and custom searches. Local settings can override new defaults. |

For a lookup error, run on the search head:

```bash
/opt/splunk/bin/splunk btool transforms list vmware_vision_normalize --app=vmware_vision --debug
/opt/splunk/bin/splunk btool props list vmware:vision:vcenter --debug
/opt/splunk/bin/splunk btool fields list cim_dataset --debug
```

Review Job Inspector and `search.log` for the affected peer. A scripted-lookup visibility problem is not, by itself, evidence that Splunk needs an upgrade.

More checks and a non-indexing lookup test:

https://github.com/majidershadi/vmware-vision/blob/main/docs/TROUBLESHOOTING.md

## 7. VMware Vision app: release notes

Version 1.1.1 fixes missing lookup results for events with boundary whitespace, recognizes explicit ESXi Hostd logout events, and classifies known Envoy, UI and SPS diagnostics more accurately. Setup and Coverage now keeps missing lookup results visible. The app retains the scoped CIM Authentication and Change mappings introduced in 1.1.0. Logout remains outside the Authentication mapping.

Embedded CRLF within an event remains a known lookup matching limitation; see the troubleshooting guide. The ingestion TA is unchanged at 1.0.2.

Before upgrading from 1.0.x, replace custom native `action` filters with `vmware_action`, review local lookup output lists and model overrides, and rebuild enabled VMware model summaries. Bundled dashboards already use the new field contract. Raw data does not need reindexing for these search-time changes.

## 8. Technical add-on: short description

Raw VMware syslog parsing for heavy forwarders or indexers: event boundaries, timestamps and encoding. Pair with VMware Vision for search-time fields and dashboards.

## 9. Technical add-on: Summary

TA-vmware-vision supplies event-boundary, timestamp and character-encoding settings for VMware syslog at the first full parsing tier. It supports the VMware Vision vCenter, ESXi, Aria and JSON sourcetypes.

Install it on a heavy forwarder that parses raw VMware events, or on indexers when they are the first full parsing tier. Use the full VMware Vision app on search heads for field normalization, dashboards, data models and CIM mappings.

This add-on contains no Python lookup, collection script, dashboard, enabled listener, index definition or forwarding destination. It does not poll VMware APIs.

## 10. Technical add-on: Details

The add-on provides `props.conf` settings for:

- `vmware:vision:vcenter`
- `vmware:vision:esxi`
- `vmware:vision:aria`
- `vmware:vision:json`

Its active configuration is limited to the add-on definition and raw parsing settings. Deployment documentation and disabled examples are included for administrators to adapt. The package has no Python runtime dependency.

Install it where raw data is first fully parsed. If an HF has already parsed the VMware events, downstream indexers do not need another copy for that data path. If indexers parse the raw input, deploy the TA there; use the cluster manager for an indexer cluster.

Search-time VMware extraction remains the responsibility of the full app on the search head and its distributed-search knowledge bundle. Installing this TA alone does not produce normalized VM fields, populate CIM or repair a missing `vmware_lookup.py` on a search peer.

The TA does not configure a syslog receiver or VMware sender. Preserve the original event and source timestamp through your collection path. Changes to parsing settings affect newly ingested data; they do not repair framing or timestamps already indexed.

VMware Vision is an independent project and is not an official VMware, Broadcom or Splunk product.

## 11. Technical add-on: Installation

1. Identify the first full parsing tier for each VMware raw-data path. Do not assume that every forwarder performs full parsing.
2. Download `TA-vmware-vision-1.0.2.tar.gz` and verify its checksum.
3. Install on the HF when it first parses the VMware syslog. If raw parsing occurs on indexers, deploy it there instead. Use the indexer cluster manager for clustered peers.
4. Keep inputs, index definitions and forwarding destinations in your managed collection configuration. Adapt only the examples needed on each tier; they are not enabled by the package.
5. Assign the appropriate `vmware:vision:*` sourcetype at collection. Do not relabel an existing source without reviewing other apps that depend on it.
6. Apply the configuration through your normal deployment/restart process. Check the effective props settings on the parsing instance.
7. Validate a small sample of newly ingested events for event boundaries, multiline preservation, timestamp/time-zone interpretation and original source attribution.
8. Install the full VMware Vision app on the search head and configure its index macro. Verify peer bundle replication before using dashboards or CIM searches.

The full app includes the same parsing settings for standalone installations, so a duplicate TA is not required there.

Deployment guide:

https://github.com/majidershadi/vmware-vision/blob/main/docs/DEPLOYMENT.md

## 12. Technical add-on: Troubleshooting

| Symptom | What to check |
|---|---|
| No data arrives | Check the VMware sender, receiver, input, forwarding destination and index. The TA does not enable any of them. |
| Events merge or split incorrectly | Confirm the actual raw parsing tier, effective sourcetype and `LINE_BREAKER`. Compare a newly collected sample with the original file/message. |
| Timestamps are wrong | Check sender/relay time zones, preserved timestamp text, `TIME_PREFIX`, lookahead and local props overrides on the parsing tier. |
| Installing on indexers changes nothing | An upstream HF may already have parsed the data. Apply parsing settings to the first full parser. |
| Old indexed events stay wrong | Parsing changes do not rewrite indexed records. Validate new events before planning any separate reingestion process. |
| VM fields, dashboards or CIM are absent | Install/configure the full search app. These functions are intentionally outside the TA. |
| Search reports a missing lookup script | Check the full app and search knowledge bundle; the ingestion TA contains no lookup script. |
| Events are duplicated | Check direct and Aria forwarding routes and duplicate monitored inputs. The TA does not deduplicate ingestion. |

Run on the first parsing tier:

```bash
/opt/splunk/bin/splunk btool props list vmware:vision:vcenter --debug
```

If the source uses another supported sourcetype, substitute its exact name. Review the file paths reported by `btool` to identify overriding configuration.

## 13. Technical add-on: release notes

Version 1.0.2 gives the TA its own beacon-and-VM icon and adds a dedicated configuration guide. Apache 2.0 licensing and enabled update checks are retained. Event boundaries, timestamp handling and character encoding are unchanged. No Python runtime, search-time lookup or enabled collection input has been added. It remains compatible with VMware Vision 1.1.1.

## 14. Contact and support text for both listings

Report bugs and feature requests through GitHub Issues:

https://github.com/majidershadi/vmware-vision/issues

Include the app and TA versions, Splunk version, deployment tier, search app context, sourcetype, a sanitized example and the expected result. For distributed lookup problems, include which search peers report the failure and the relevant sanitized `search.log` messages. Do not include passwords, tokens, private keys or unredacted customer logs.

Support is provided by the project maintainer through the public issue tracker. No response-time SLA or paid support service is included. Report sensitive security issues through the private reporting option if available, or the maintainer's website contact rather than a public issue.

## 15. URLs for the remaining fields

| Field | Value |
|---|---|
| Source code | https://github.com/majidershadi/vmware-vision |
| App download / release notes | https://github.com/majidershadi/vmware-vision/releases/tag/v1.1.1 |
| TA download / release notes | https://github.com/majidershadi/vmware-vision/releases/tag/ta-v1.0.2 |
| Documentation | https://github.com/majidershadi/vmware-vision/blob/main/docs/INSTALLATION.md |
| TA documentation | https://github.com/majidershadi/vmware-vision/blob/main/docs/TA_CONFIGURATION.md |
| Data-model setup | https://github.com/majidershadi/vmware-vision/blob/main/docs/DATA_MODELS.md |
| CIM setup | https://github.com/majidershadi/vmware-vision/blob/main/docs/CIM.md |
| Troubleshooting | https://github.com/majidershadi/vmware-vision/blob/main/docs/TROUBLESHOOTING.md |
| Build from source | https://github.com/majidershadi/vmware-vision/blob/main/docs/BUILD.md |
| Support | https://github.com/majidershadi/vmware-vision/issues |
| License | https://github.com/majidershadi/vmware-vision/blob/main/LICENSE |
| Introduction / project website | https://majidershadi.github.io/articles/vmware-vision-1-1/ |

## 16. Icons, screenshots and reviewer notes

Use the eye-and-VM image for the app and the beacon-and-VM image for the TA. The 512 × 512 listing images are `docs/assets/vmware-vision.png` and `docs/assets/ta-vmware-vision.png`. App launcher icons are in `package/static/`; TA launcher icons are in `assets/ta/`. Follow the dimensions requested by the upload form. Screenshots, if supplied, must show the actual running app and should use suitable sample data. The ingestion TA has no dashboard to screenshot.

Reviewer notes for the app:

> Search-time normalization runs as an automatic scripted lookup using the Python standard library. The script is explicitly shared so it can run outside the app. The parser and CIM module are included in the package. Lookup-derived fields declare INDEXED_VALUE=false to prevent raw-term filtering from discarding eligible records. CIM mappings are restricted to explicit supported event outcomes. UCC provides the logging configuration page; the app does not poll external VMware APIs. SDK 2.1.1 remains pinned for Python 3.9 compatibility; the native inspection report and validation guide document the advisory warnings.

Reviewer notes for the TA:

> This add-on contains raw parsing configuration, branding, licensing and administrator documentation. It has no executable collection code, search-time lookup, dashboard, data model, enabled input, index definition or output configuration. Search-time content is distributed separately in the VMware Vision app.

The earlier candidate passed AppInspect 4.3.1 on Linux, but Splunkbase separately rejected its disabled update-check setting. The corrected packages set `check_for_updates = true`, and the release preflight now checks this setting before AppInspect. Consult the reports and checksums supplied with the corrected archives; earlier reports describe earlier package bytes. Local inspection is not a claim that Splunkbase or Splunk Cloud has approved either package.

The live validation used standalone Splunk Enterprise 10.4.1 and CIM 8.7.0. Fifty-five source tests passed under Splunk Python 3.9 and 3.13. Synthetic event checks confirmed one Authentication record, eleven Change records and four intentional exclusions. These are functional checks, not production load tests or a complete distributed/ES acceptance test.


## App 1.1.1 patch notes

Fixes missing lookup fields for records with leading or trailing whitespace, recognizes explicit Hostd logout events, improves known service diagnostic classification, and exposes missing lookup results in coverage charts. The original raw events remain unchanged. TA 1.0.2 needs no update. Rebuild affected accelerated summaries for historical corrections; reindexing is not required. Embedded CRLF lookup matching remains a documented limitation.
