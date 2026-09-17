# VMware data models and acceleration

## Models and scope

| Model | Root dataset | Intended use |
|---|---|---|
| `VMware_Vision` | `Events` | Detailed event fields; child datasets for VM changes, authentication, alarms and failures |
| `VMware_Vision_Activity` | `Activity` | Compact dimensions for aggregate activity trends |

Both use `vmware_vision_indexes` through the VMware sourcetype scope and require `record_kind=event`. Diagnostics remain available in ordinary searches and coverage views. Acceleration is disabled by default.

These are custom models. They do not require Splunk_SA_CIM, and CIM Setup does not set their index scope. For CIM's models, read [CIM.md](CIM.md).

## 1. Set the index macro

In **Settings → Advanced search → Search macros**, select `vmware_vision` and edit `vmware_vision_indexes`:

```spl
(index=vmware OR index=vmware_syslog)
```

Verify searching-role permissions and the presence of correctly assigned sourcetypes before changing model settings.

## 2. Test without acceleration

Use a time range containing known events:

```spl
| datamodel VMware_Vision Events flat strict_fields=false
| table _time vcenter vm_name event_type vmware_action status
| head 30
```

```spl
| datamodel VMware_Vision_Activity Activity flat strict_fields=false
| stats count by vmware_action status
```

`flat` gives unprefixed field names. `strict_fields=false` includes model, calculated and lookup fields. Zero rows need investigation of source data, scope, permissions and normalization before acceleration is enabled.

## 3. Enable the compact activity model

Open **Settings → Data models**, choose VMware Vision, and expand **VMware Vision Activity**. Use **Edit → Edit Acceleration**, select **Accelerate**, and choose a summary range that fits your searches and capacity. Start with a short range and observe cost before widening it.

Equivalent managed configuration in the app's `local/datamodels.conf`:

```ini
[VMware_Vision_Activity]
acceleration = true
acceleration.earliest_time = -7d
```

Seven days is an example, not a requirement. Summary range is not raw index retention. Leave the larger full model disabled unless a workload needs it and you have measured its storage and scheduler cost.

## 4. Confirm summary coverage

Wait for the model status to show progress and compare results over a completed time window:

```spl
| tstats summariesonly=false count FROM datamodel=VMware_Vision_Activity.Activity
  WHERE earliest=-24h latest=-1h
  BY Activity.vmware_action Activity.status
```

```spl
| tstats summariesonly=true count FROM datamodel=VMware_Vision_Activity.Activity
  WHERE earliest=-24h latest=-1h
  BY Activity.vmware_action Activity.status
```

The summary-only query can omit recent or older unsummarized events. Compare a covered interval, not simply two searches with different effective coverage. A 100% status does not prove that the chosen index scope contains the expected records.

Open **Accelerated Activity**, choose the time window and origin, and click **Submit**. Before that click, “Search is waiting for input” is expected. A panel query such as `stats sum(events) AS events` is a post-process query that depends on the dashboard's transforming base search; it is not a standalone search.

## 5. Rebuild after relevant changes

Rebuild enabled model summaries after changing index scope, parsing/mapping semantics or the model schema. For an upgrade to 1.1.0, the compact model now uses `Activity.vmware_action` in place of `Activity.action`.

Use the model's **Rebuild** control during an appropriate maintenance window. Rebuilding consumes resources and temporarily reduces available summary coverage. Keep raw-backed searches available while it runs.

## Performance and counting

The compact model omits raw text, VM identity and detailed change objects. It cannot answer “what was the exact last change to this VM?” Use the detailed audit views for that question.

Audit panels deduplicate event identity where supplied. Model summaries count received records, including duplicated delivery. Different totals can therefore be expected. Narrow time windows, explicit indexes, event classification and shared dashboard base searches help control the cost of raw-backed views.
