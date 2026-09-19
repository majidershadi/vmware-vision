# Troubleshooting

Start with a small time window and one source whose original event is available. Capture the app version, Splunk version, search app context and sourcetype before changing settings.

| Symptom | Check |
|---|---|
| No data in any panel | Time window, index macro, role index access, exact sourcetype and collection path |
| Mostly diagnostics or unknown actions | Inspect actual event classes; high-volume service logs are not all VM operations |
| Missing VM name/ID | Check source fields and multiple-VM ambiguity; the parser does not invent identity |
| Missing old/new values | Confirm whether the source event supplies configuration details |
| “Search is waiting for input” | Click Submit; inspect unresolved dashboard tokens and base-search dependencies |
| Empty accelerated panels | Verify the custom Activity model, index scope, summary range and covered time window |
| CIM models empty | Verify tags, CIM index allowlists, permissions and `fields.conf` for computed values |
| Different audit and summary totals | Check duplicate delivery and summary coverage; summaries are not audit deduplication |
| Data missing only after an upgrade | Review local props, transform, fields, metadata and model overrides |

## Distinguish missing fields from unsupported records

The [coverage definitions and known 1.1.1 audit limitations](../README.md#reading-coverage-results) explain each label. In particular, missing VM identity on an event candidate is not the same as absent lookup output. The current parser can miss names supplied by the message, and diagnostic mentions of an event class can be misclassified as completed operations. Reconfiguration fragments can also produce an incorrect event ID from nested `key` values. These are unresolved code issues, not conditions corrected by this documentation update.

## Lookup errors outside VMware Vision

If Splunk reports `Could not load lookup=LOOKUP-vmware_vision` or cannot find `vmware_lookup.py`, check effective configuration on the search head:

```bash
/opt/splunk/bin/splunk btool transforms list vmware_vision_normalize --app=vmware_vision --debug
/opt/splunk/bin/splunk btool props list vmware:vision:vcenter --debug
/opt/splunk/bin/splunk btool fields list cim_dataset --debug
/opt/splunk/bin/splunk btool check
```

The lookup definition, props and `searchscripts/vmware_lookup.py` metadata must be visible outside the app. The script and `vmware_vision_parser.py` / `vmware_vision_cim.py` must exist in the app's `bin/` directory. Check local metadata overrides and distributed-search bundle exclusions. Do not solve a visibility problem by upgrading Splunk without establishing the cause.

Use this non-indexing diagnostic from Search & Reporting:

```spl
| makeresults
| eval _raw="eventType=VmPoweredOnEvent vm_name=lookup-check vm_id=vm-1 vcenter=lookup-check",
       host="lookup-check", sourcetype="vmware:vision:vcenter"
| lookup local=true vmware_vision_normalize _raw host sourcetype
  OUTPUT parser_version cim_dataset vmware_action action status
| table parser_version cim_dataset vmware_action action status
```

Expected values are `1.1.1`, `Change`, `power_on`, `started`, `success`. This checks local execution only. A real indexed search is still needed to test peer execution and automatic lookup application.

## Fields exist in a table but a filter returns nothing

Compare the generated fields with the original event. Computed values need not appear in raw text. Verify that the app's `fields.conf` is deployed and exported, especially for `cim_dataset`, `record_kind`, `parser_status`, `action`, `status` and `vmware_action`. A local override can reintroduce incorrect raw-term filtering.

## Useful evidence

Review Job Inspector's search messages and the relevant `search.log` entries. For distributed failures, identify the affected search peer and its bundle version. Share only sanitized log excerpts. Never include authentication headers, session tokens, passwords or private keys in a GitHub issue.


## Missing lookup fields when the raw record ends with whitespace

Versions through 1.1.0 used minimally quoted CSV output. In the lab, Splunk failed to match some returned lookup keys when `_raw` had leading or trailing whitespace. Explicitly trimming a temporary input field made these records match, while the original lookup returned no parser fields. Version 1.1.1 quotes the three input keys in CSV and preserves input line endings. It does not trim or rewrite indexed events.

Upgrade the full app on the search tier using your normal deployment process. For a search head cluster, use the deployer. Preserve local settings and review overrides of `LOOKUP-vmware_vision`, transforms, fields and script-sharing metadata. Start a new job after the app and search bundle have refreshed. Confirm `parser_version=1.1.1` in VMware Vision and Search & Reporting, including results from every peer that holds matching records. The ingestion TA remains 1.0.2.

No reindexing is needed. Rebuild affected VMware and CIM acceleration summaries if you need historical summary results to include corrected normalization; plan for the rebuild cost. Unaccelerated searches apply the new lookup to existing data immediately after configuration and bundle refresh.

The coverage chart now labels absent classification fields as `lookup_missing`. `unclassified` means the parser returned a result but did not recognize the message. `diagnostic` means a supported service-log shape was recognized; it is not evidence of a completed VM change.

### Remaining embedded-CRLF limitation


CRLF means a carriage return followed by a line feed (`\r\n`); LF is a line feed (`\n`). This test deliberately used CRLF inside a synthetic event to check how the CSV lookup handles unusual input. It does not mean VMware Vision requires CRLF or that the VMware systems use Windows. No collection setting or indexed event was changed to add it. A collector, relay, export or payload can introduce line endings independently of the sender's operating system, but the reported production sample established trailing whitespace, not embedded CRLF.

The live Splunk test still returned no match for a synthetic `_raw` value containing embedded CRLF line endings, despite the script preserving those bytes and quoting the CSV fields. Plain single-line records, leading/trailing spaces and tabs, commas, quotes, Unicode and LF multiline records passed. This CRLF case is a known limitation of the tested external lookup path; do not treat 1.1.1 as a fix for every possible CSV matching problem. Retain the original raw record and investigate the search log if `lookup_missing` remains. Do not reindex or alter production collection solely to hide this condition.


### Check the upgrade on each search peer

Use the indexes and time range containing your known samples. Run a new search in both VMware Vision and Search & Reporting:

```spl
(index=vmware-esxi OR index=vmware-vcenter OR index=log-insight)
sourcetype=vmware:vision:*
| eval version=coalesce(parser_version,"MISSING"),
       kind=coalesce(record_kind,"MISSING")
| stats count AS events by splunk_server sourcetype version kind
```

Each normalized row should report version `1.1.1`. `unclassified` is an unsupported message shape, while `MISSING` requires checking lookup execution, matching and the knowledge bundle. A diagnostic does not need a VM identity. Unknown records remain visible; do not turn them into successful changes to improve a coverage percentage.
