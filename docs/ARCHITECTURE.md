# Parsing, fields and boundaries

## Processing path

The ingestion TA runs at the first full parsing tier. It controls event boundaries, timestamp discovery, truncation and encoding. The full search app then uses an automatic external lookup to normalize each raw message, its host and sourcetype.

`vmware_lookup.py` implements Splunk's CSV lookup interface. `vmware_vision_parser.py` recognizes source formats and extracts VMware fields. `vmware_vision_cim.py` applies a conservative allowlist for CIM mappings. The lookup makes no network calls, writes no files and needs no VMware credentials.

The UCC configuration page manages application logging. It does not configure a vCenter connection, enable a listener or collect API inventory.

## Recognized formats

- vCenter bracketed `Event [...]` records with event class, actor, event time and message.
- JSON objects with supported event fields and embedded event messages.
- Explicit key/value event fields.
- RFC 5424 and common relay-wrapped syslog envelopes.
- Common VMware diagnostic service messages, classified separately from events.

Assigning the Aria or ESXi sourcetype does not imply every message from those products has a lifecycle mapping. Unsupported event classes stay visible as `unmapped_event_type`; unrecognized text stays unclassified. A service principal such as `com.vmware.vim.eam` is not treated as an event class.

## Main fields

| Fields | Meaning |
|---|---|
| `event_type`, `event_id`, `event_time`, `event_chain_id` | Event class and available source identifiers |
| `vcenter`, `component`, `esxi_host` | Normalized origin and component/host context |
| `vm_name`, `vm_id`, `vm_uuid`, `vm_key` | VM identifiers; the key is scoped to the origin |
| `identity_quality`, `vm_reference_count` | Identity source and ambiguity indicators |
| `user`, `src_ip` | Actor and client IP when present |
| `vmware_action`, `category`, `status` | Native operation, grouping and outcome |
| `observed_state` | State from a completed state-changing event |
| `change_details`, `change_fields`, `old_value`, `new_value` | Details explicitly available in the event |
| `record_kind`, `parser_status`, `parser_format`, `parser_version` | Classification and parser diagnostics |
| `cim_dataset`, `action` | CIM eligibility and standard action for mapped events |

See [event-map.csv](event-map.csv) for the native event-class map and [CIM.md](CIM.md) for the narrower CIM scope.

## Identity and event ordering

VM identity prefers UUID, then managed-object ID, then name, and includes vCenter/origin scope. A managed-object ID is not globally unique across vCenters. Name-only identity can split when a VM is renamed or merge if a name is reused. Multiple incidental VM references are not arbitrarily assigned to one primary VM.

The latest-activity table sorts and selects a complete event row, keeping its actor, action, status and message together. Last observed state uses successful state-changing events within the selected time window. It does not infer live inventory from silence.

The audit deduplication key uses source-scoped event ID and event time when available. Its fallback uses raw text, host and Splunk event time. Relay changes to those values can prevent deduplication; do not assume exactly-once delivery.

## Search behavior

Props, transforms, selected eventtypes/tags and the lookup script are shared across search apps. The script and its two helper modules must also reach distributed search peers.

`fields.conf` sets `INDEXED_VALUE=false` for computed fields whose values may not exist literally in raw text. Without it, base filters such as `cim_dataset=Authentication` can reject records before the lookup runs. Shared field names such as `action` and `status` may cause less raw-term prefiltering for other sources too. Field values and indexed extraction settings are not overwritten by this metadata. Use explicit index, sourcetype and time constraints.

## What this release does not provide

- vCenter or Aria API polling, backfill through APIs, or inventory reconciliation.
- Live state when no corresponding event was received.
- Old/new configuration values absent from the source log.
- Complete mappings for every ESXi, Aria or future VMware event type.
- Automatic ES detection enablement, inventory enrichment or asset/identity ownership fields.
- Guaranteed detection of activity not forwarded by the source.

API polling may be added in a future release. No API collection schedule is promised.
