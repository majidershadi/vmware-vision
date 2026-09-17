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

Expected values are `1.1.0`, `Change`, `power_on`, `started`, `success`. This checks local execution only. A real indexed search is still needed to test peer execution and automatic lookup application.

## Fields exist in a table but a filter returns nothing

Compare the generated fields with the original event. Computed values need not appear in raw text. Verify that the app's `fields.conf` is deployed and exported, especially for `cim_dataset`, `record_kind`, `parser_status`, `action`, `status` and `vmware_action`. A local override can reintroduce incorrect raw-term filtering.

## Useful evidence

Review Job Inspector's search messages and the relevant `search.log` entries. For distributed failures, identify the affected search peer and its bundle version. Share only sanitized log excerpts. Never include authentication headers, session tokens, passwords or private keys in a GitHub issue.
