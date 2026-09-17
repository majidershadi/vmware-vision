# Install and configure VMware Vision

## 1. Plan the data path

Use your existing durable syslog receiver to collect VMware logs, then forward them to Splunk. VMware Vision supplies parsing and search content; it does not start a listener or configure VMware senders.

```text
vCenter / ESXi / Aria → syslog receiver → HF or indexer parsing → indexers
                                                                    ↓
                                                   VMware Vision on search heads
```

vCenter event records are the primary source for VM lifecycle and configuration auditing. ESXi logs add host detail and diagnostics. Aria can relay VMware event records, but its own appliance logs are not a substitute for vCenter events. Check whether both direct forwarding and Aria forwarding deliver the same event before enabling both paths.

## 2. Create or choose the index

The examples use `vmware`. You can use an existing index, including `main`, if that matches your retention and access model. Create a new index on the indexing tier, not only on a search head.

Example standalone index definition:

```ini
[vmware]
homePath = $SPLUNK_DB/vmware/db
coldPath = $SPLUNK_DB/vmware/colddb
thawedPath = $SPLUNK_DB/vmware/thaweddb
```

Apply your own retention, storage limits and role permissions. For an indexer cluster use its cluster manager and the [deployment guide](DEPLOYMENT.md).

## 3. Install the two packages where needed

On a standalone instance, install the full app through **Apps → Manage Apps → Install app from file**. Upload `vmware_vision-1.1.0.tar.gz` and restart when Splunk requests it.

For distributed deployments, install the full app on search heads. Install `TA-vmware-vision-1.0.1.tar.gz` on the first full parsing tier for each raw input path. If an HF parses all events, indexers do not need another copy solely to parse those already cooked events. See the tier table in [DEPLOYMENT.md](DEPLOYMENT.md).

Do not extract either archive into a second nested directory. The installed full app should be `$SPLUNK_HOME/etc/apps/vmware_vision/default/app.conf`.

## 4. Assign the sourcetype

| Sourcetype | Use for |
|---|---|
| `vmware:vision:vcenter` | Native vCenter syslog, including bracketed event records |
| `vmware:vision:aria` | Aria-forwarded VMware messages |
| `vmware:vision:esxi` | ESXi logs |
| `vmware:vision:json` | Supported JSON event envelopes, one object per line |

Example monitored file input on a collector/HF:

```ini
[monitor:///var/log/remote/vcenter/*.log]
index = vmware
sourcetype = vmware:vision:vcenter
disabled = 0
```

Keep input and output configuration in your own managed collection app. Samples under `docs/ta-examples/` are inactive until you adapt and enable them. Preserve original source timestamps, time zones and host information when relaying logs.

Existing indexed data is not reparsed by installing a TA. Correct future framing/timestamps on the parsing tier. Search-time normalization can apply to existing raw events with matching sourcetypes. If retaining a custom sourcetype, copy the complete automatic lookup stanza to that sourcetype and extend your search scope and eventtype selectors deliberately; an index macro alone does not change sourcetype selection.

## 5. Set the VMware search indexes

Open **Settings → Advanced search → Search macros**, select app **VMware Vision**, and edit `vmware_vision_indexes`.

For one index:

```spl
index=vmware
```

For several indexes:

```spl
(index=main OR index=vmware_syslog)
```

Alternatively merge into `vmware_vision/local/macros.conf`:

```ini
[vmware_vision_indexes]
definition = (index=main OR index=vmware_syslog)
iseval = 0
```

Do not edit the default file. Ensure the searching role can read every selected index. Index macros do not grant permissions.

## 6. Validate a small sample

Open Search in VMware Vision and select a time range with known VMware activity:

```spl
`vmware_vision_events`
| stats count by sourcetype parser_version parser_status record_kind
```

Then inspect specific records:

```spl
`vmware_vision_events`
| head 30
| table _time host sourcetype event_type vm_name vm_id user vmware_action action status parser_status
```

Expect parser version `1.1.0`. `record_kind=diagnostic` is normal for service logs; it is not a failed VM extraction. An unknown event class stays visible rather than being guessed into a successful operation.

Repeat a search from **Search & Reporting** to verify cross-app lookup visibility:

```spl
index=vmware sourcetype=vmware:vision:*
| stats count by vmware_action status
```

## 7. Use the dashboards

Start with **Setup and Coverage** to check freshness, classification and missing identities. Then use **VMware Overview** and **VM History**. The vCenter filter accepts `*` for all origins. VM History matches the supplied VM name or ID exactly, ignoring case for names.

Audit panels deduplicate copies using available event identity. Latest state only uses completed state-changing records in the selected time window. Names alone can merge reused names or split a renamed VM; prefer UUID or vCenter-scoped managed-object ID.

## 8. Configure models and CIM

Follow [DATA_MODELS.md](DATA_MODELS.md) for the two custom VMware models and optional acceleration. Follow [CIM.md](CIM.md) for Authentication and Change. The custom VMware index macro and CIM index macros are independent.

## 9. Upgrade safely

Back up the installed app's `local/` directory and `metadata/local.meta`. Upgrade through the same deployment mechanism you used to install it. Review local overrides before restarting.

For upgrades from 1.0.x, replace native `action` references with `vmware_action` in custom searches and alerts. A local props lookup output list can hide newly added fields; compare it with the full new default. Rebuild enabled VMware summaries because the compact model's action dimension changed. Existing raw events do not need reindexing.

Restore the previous app and local configuration to roll back. Revert custom searches and rebuild affected summaries to match the restored schema. Do not delete indexes to roll back a search app.
