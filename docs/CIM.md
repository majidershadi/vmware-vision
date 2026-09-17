# VMware Vision 1.1.0: CIM setup and upgrade

This release adds scoped mappings into **Authentication.Authentication** and **Change.All_Changes**. It preserves VMware operations in `vmware_action`, while `action` uses CIM values for eligible events. The bundled dashboards and reports use `vmware_action`.

The lab has Splunk Enterprise 10.4.1 and Splunk_SA_CIM 8.7.0. Python 3.9 and 3.13 are declared runtimes; Splunk 10.0.2 remains a compatibility target, not a completed distributed acceptance test. These mappings do not establish Splunk certification or validate every Enterprise Security detection. See [VALIDATION.md](VALIDATION.md) for the scope of completed checks.

## 1. Install on the correct tier

| Tier | Required content |
|---|---|
| Standalone Splunk | VMware Vision 1.1.0 and Splunk_SA_CIM |
| Search head / search head cluster | VMware Vision 1.1.0 and the CIM version supported by that Splunk/ES installation |
| Heavy forwarder | TA-vmware-vision 1.0.1 for raw parsing |
| Indexers | Index configuration; TA where raw parsing occurs; search-time knowledge comes from the search head bundle |

For Enterprise Security, use its supported bundled CIM version; do not replace it independently just to match this lab. Deploy search head cluster apps through the deployer. Deploy indexer parsing configuration through the cluster manager. Do not copy the whole dashboard app or install CIM on an HF solely for this integration.

## 2. Back up and upgrade VMware Vision

1. Back up the installed `vmware_vision` app, including `local/` and `metadata/local.meta`.
2. Record the current VMware index macro, custom searches and data-model acceleration settings.
3. Upload `vmware_vision-1.1.0.tar.gz` using **Apps → Manage Apps → Install app from file**, selecting the upgrade option. Follow your normal deployment process for clustered environments.
4. Review local overrides. A local `LOOKUP-vmware_vision` output list can hide the new fields. Compare it with the new default; preserve intentional changes, but include the full new output list. Also inspect local transforms, metadata, dashboards and model definitions that override defaults.
5. Restart Splunk when requested, or use your approved knowledge-object reload procedure. Start a new search job for validation.

No reindexing is needed: the automatic lookup normalizes existing events at search time. The release does not change inputs or index retention.

### Migrate custom searches before relying on their totals

Native operation names now reside in `vmware_action`:

```spl
index=vmware sourcetype=vmware:vision:* vmware_action=power_on status=success
| table _time vcenter vm_name user vmware_action action status
```

Change a custom filter such as `action=power_on` to `vmware_action=power_on`. Make the same adjustment in custom saved searches, panels and alerts. For example, `action=modified` now groups several different VMware operations; use `vmware_action` to distinguish reconfiguration, rename and migration.

The compact **VMware Vision Activity** model replaces `Activity.action` with `Activity.vmware_action`. The full **VMware Vision** model includes both fields. Rebuild enabled summaries for both custom models after upgrading; previously summarized action values must not be mixed with this release. Review custom model overrides before rebuilding. The app does not enable acceleration automatically.

## 3. Check automatic normalization first

In **Search & Reporting**, run this over a period with VMware events, substituting your index:

```spl
index=vmware sourcetype=vmware:vision:*
| stats count by parser_version cim_dataset event_type vmware_action action status
```

Expect `parser_version=1.1.0`. Events without `cim_dataset` are omitted by this particular `stats by` search. Inspect exclusions separately:

```spl
index=vmware sourcetype=vmware:vision:*
| where isnull(cim_dataset) OR cim_dataset=""
| stats count by record_kind event_type vmware_action
```

If lookup errors recur, follow the [lookup troubleshooting guide](TROUBLESHOOTING.md). The globally shared props, transform and `searchscripts/vmware_lookup.py` metadata remain necessary. The new module `bin/vmware_vision_cim.py` must also be in the search bundle; it is imported by the lookup, not registered as a separate scripted lookup.

## 4. Introduce your indexes to CIM

The VMware macro and CIM macros serve different models:

| Scope | Index macro |
|---|---|
| VMware Vision dashboards and custom models | `vmware_vision_indexes` in `vmware_vision` |
| CIM Authentication | `cim_Authentication_indexes` in `Splunk_SA_CIM` |
| CIM Change | `cim_Change_indexes` in `Splunk_SA_CIM` |

Setting the VMware macro does **not** update CIM. Adding an index to CIM only sets search scope; tags and field mappings determine eligible records.

### Splunk Web procedure

1. Open **Apps → Splunk Common Information Model**, then its setup page: `/en-US/app/Splunk_SA_CIM/cim_setup`.
2. Select **Authentication** and add your VMware index names to **Indexes allowlist** (comma-separated in CIM 8.7.0). Preserve indexes already used by other authentication sources.
3. Select **Change** and add the same VMware index names while preserving existing change sources.
4. Save the configuration. Keep acceleration off until the searches below return the expected data.
5. If your CIM version's setup layout differs, use **Settings → Advanced search → Search macros**. Select the `Splunk_SA_CIM` app, locate the two exact macro names above, and edit their definitions. Preserve the existing owner/sharing.

Example definitions for a deployment with VMware in `main` and `vmware_syslog`:

```ini
[cim_Authentication_indexes]
definition = (index=main OR index=vmware_syslog)

[cim_Change_indexes]
definition = (index=main OR index=vmware_syslog)
```

A UI index picker expects **index names**; the macro editor expects the complete **SPL expression** above. Do not paste SPL into an index-name picker.

### Configuration-file procedure

Merge the stanzas into `$SPLUNK_HOME/etc/apps/Splunk_SA_CIM/local/macros.conf` using your normal configuration management. Never edit `default/macros.conf`. Include all existing required indexes in each definition; the example is not permission to replace an organization's existing index scope. For a search head cluster, stage changes through its supported deployment process.

Verify the effective configuration:

```bash
/opt/splunk/bin/splunk btool macros list cim_Authentication_indexes --app=Splunk_SA_CIM --debug
/opt/splunk/bin/splunk btool macros list cim_Change_indexes --app=Splunk_SA_CIM --debug
```

Index macros do not grant access. The search user and acceleration owner must already have permission to search the selected indexes. Keep synthetic validation records outside production model scope.

## 5. Verify tags, then data models

Run in Search & Reporting with a suitable time range:

```spl
index=vmware sourcetype=vmware:vision:* tag=authentication
| table _time event_type user src dest action vmware_action reason
```

```spl
index=vmware sourcetype=vmware:vision:* tag=change
| table _time event_type user object object_id action vmware_action status change_type
```

Then verify actual model membership. `flat strict_fields=false` returns unprefixed fields including model calculations and lookup outputs:

```spl
| datamodel Authentication Authentication flat strict_fields=false
| search sourcetype=vmware:vision:*
| stats count by action app
```

```spl
| datamodel Change All_Changes flat strict_fields=false
| search sourcetype=vmware:vision:*
| stats count by action status change_type
```

Zero results do not by themselves mean a parser failure. Check the selected time range, index permissions, macro definitions and source events. CIM 8.7.0's Authentication root intentionally excludes successful logins for usernames ending in `$`; compare like-for-like when reconciling raw and model counts.

## 6. Enable and verify acceleration separately

1. Open **Settings → Data models** and select the CIM app.
2. Edit acceleration for **Authentication** or **Change**, as required by your ES deployment and available capacity.
3. Start with a summary range justified by your searches and retention. Do not enable every CIM model or a one-year range simply because it is available.
4. Wait for summarization to cover a completed time window. Inspect model status and summary size.
5. For a model that was accelerated before these mappings/index changes, rebuild its summaries through **Settings → Data models**. Otherwise historical summaries may omit the new VMware events. Rebuilding consumes resources and temporarily reduces summary coverage; schedule it appropriately.
6. Test raw-backed results first, then summary-only results over the same covered window:

```spl
| tstats summariesonly=false count FROM datamodel=Authentication.Authentication
  WHERE earliest=-24h latest=-1h Authentication.app=vmware_vcenter
  BY Authentication.action
```

```spl
| tstats summariesonly=true count FROM datamodel=Authentication.Authentication
  WHERE earliest=-24h latest=-1h Authentication.app=vmware_vcenter
  BY Authentication.action
```

```spl
| tstats summariesonly=true count FROM datamodel=Change.All_Changes
  WHERE earliest=-24h latest=-1h All_Changes.object_category=virtual_machine
  BY All_Changes.action All_Changes.status
```

The Change summary query may include other vendors that use `virtual_machine`; narrow by `All_Changes.dvc` to a known VMware origin for acceptance. Summary-only searches omit unsummarized recent/old events. CIM counts received records and may include duplicated delivery; VMware audit panels deduplicate event IDs, so their totals are not automatically comparable.

Enabling CIM acceleration does not enable the separate **VMware Vision Activity** model. Its Accelerated Activity dashboard still needs that custom model enabled and its **Submit** button clicked.

## 7. Know the mapping boundaries

| Input | CIM behavior |
|---|---|
| Explicit successful login / bad username / invalid login | Authentication; action is success or failure |
| VM create, deploy, clone, removal | Change; created or deleted |
| VM power-on/off outcome, including explicit failure events | Change; started or stopped; status distinguishes success/failure |
| VM suspend, registration, reconfiguration, rename, migration | Change; modified, with a specific change_type |
| VM snapshot operations | Change to the VM; modified / snapshot, without inventing a snapshot ID |
| Explicit failed reset | Change; restarted with failure; no completed power state implied |
| Logout, requested operations, generic tasks, diagnostics, unknown types | Excluded from these CIM mappings; remain searchable in VMware Vision |
| Permission/role, alarm, host and datastore events | Retained in VMware dashboards; excluded from this initial CIM scope |

`user` is the actor for these VM changes. `dest` and `dvc` identify the normalized vCenter origin; `object` is the VM name and `object_id` prefers VM UUID, then MOID. MOIDs are only unique within a vCenter: correlate with `dvc`. `src` comes from the client IP only when supplied/extracted; the relay address is not substituted for the client. `signature` identifies the event class. Missing authentication method, command, object IDs and before/after values are not fabricated. Aria transport alone does not make an appliance diagnostic message an authentication event.

Before enabling an ES detection, check its exact required fields and datasets against actual source records. Installing CIM and mapping these two models does not validate all ES detections or provide VMware inventory.

## Search behavior and performance

The package declares `INDEXED_VALUE=false` for lookup-generated values such as `cim_dataset`, `record_kind`, `action`, `status` and `vmware_action`. Otherwise Splunk may require words such as `Authentication` or `mapped` in the original log text and discard valid events before the lookup runs. This fixes base-search tag filters and model constraints without changing indexed events.

Some names, including `action` and `status`, are shared CIM fields. Their exported search metadata can reduce raw-term prefiltering for searches on other sources too. It does not overwrite other sources' field values or change their `INDEXED` setting. Constrain indexes, sourcetypes and time windows; validate costs on production volumes and use acceleration for aggregate workloads. Do not remove these declarations simply to reduce scans, because doing so can silently omit valid events.

## 8. Roll back if required

Restore the backed-up app using the same deployment process, including any local overrides changed for the upgrade. Restore the previous CIM macro definitions if you changed scope. Restore custom searches to the field contract of the restored release, then rebuild summaries for any reverted model definitions. Indexed raw events are unchanged.

Reference definitions: [Splunk Authentication](https://help.splunk.com/en/splunk-enterprise/common-information-model/6.1/data-models/authentication) and [Splunk Change](https://help.splunk.com/splunk-enterprise/common-information-model/6.1/data-models/change). Implementation was also checked against the installed CIM 8.7.0 model definitions.
