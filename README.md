# VMware Vision for Splunk

<img src="docs/assets/vmware-vision.png" width="96" height="96" alt="VMware Vision eye and virtual machine icon">

VMware Vision turns recorded VMware syslog events into a VM activity trail: creation, changes, removal, power operations, migrations, snapshots, users and failures.

The app works with logs already collected from vCenter, ESXi and Aria. It does not poll VMware APIs, collect live inventory or change VMware configuration. API polling may be considered for a future release; it is not included in version 1.1.0.

## Packages

| Package | Version | Install on |
|---|---|---|
| `vmware_vision` | 1.1.0 | Search heads or a standalone Splunk instance |
| `TA-vmware-vision` | 1.0.1 | The heavy forwarder or indexers that first parse raw VMware logs |

The technical add-on supplies event boundaries, timestamp settings and character encoding. Search-time field extraction, dashboards, reports and CIM mappings belong to the full app. Neither package enables a listener, creates an index or configures forwarding.

Download installation archives from [Releases](https://github.com/majidershadi/vmware-vision/releases). The source ZIP is a development tree and cannot be installed directly as a Splunk app.

## Start here

1. Read [installation and configuration](docs/INSTALLATION.md).
2. Choose the correct tiers using [distributed deployment](docs/DEPLOYMENT.md).
3. Set `vmware_vision_indexes` to your VMware indexes.
4. Check parsing with a small time window before enabling [data-model acceleration](docs/DATA_MODELS.md).
5. For Enterprise Security, follow [CIM Authentication and Change setup](docs/CIM.md).

For development, see [building from source](docs/BUILD.md), [parser design](docs/ARCHITECTURE.md) and [troubleshooting](docs/TROUBLESHOOTING.md).

## Views

| View | Purpose |
|---|---|
| VMware Overview | Counts, categories, latest VM activity, users and failures |
| VM History | Event trail and last successfully observed state |
| Configuration and Change Audit | Configuration, rename, migration and snapshot details |
| Operations and Security | Authentication, permissions, alarms, host events and tasks |
| Setup and Coverage | Source freshness, parsing status and identity quality |
| Accelerated Activity | Optional aggregate trends from summarized data |
| Configuration | UCC application logging settings |

`vmware_action` keeps native operation names such as `power_on` and `reconfigured`. For eligible CIM events, `action` contains the CIM value, such as `started`, `modified`, `success` or `failure`.

## Compatibility and limits

The standalone validation environment uses Splunk Enterprise 10.4.1 with Splunk_SA_CIM 8.7.0. Runtime checks cover Python 3.9 and 3.13. Splunk 10.0.2 remains a compatibility target; distributed acceptance on that release is not claimed. On Splunk versions that support `python.required`, the highest installed declared runtime is selected. The legacy fallback is `python.version=python3.9`.

The VMware dashboards and custom models do not require CIM. CIM is required to use its Authentication and Change models. Use the CIM version supported by your Enterprise Security deployment.

Missing source fields stay missing. A request is not treated as a completed operation. Last observed state is not current inventory. Aria appliance diagnostics alone do not provide a complete VM audit history. See [coverage and limitations](docs/ARCHITECTURE.md).

AppInspect reports accompany release artifacts. Passing local checks is not a claim of Splunkbase approval, Splunk Cloud certification or support for every ES detection.

## Upgrading from 1.0.x

Back up local configuration. Update custom searches from native `action` filters to `vmware_action`, review local lookup output lists, and rebuild any enabled VMware model summaries. The bundled dashboards are already migrated. The 1.0.1 ingestion add-on changes packaging and licensing; its raw parsing settings are unchanged from 1.0.0.

## License and support

Copyright 2026 Majid Ershadi. Licensed under [Apache 2.0](LICENSE). Bundled dependencies retain their own licenses.

Use [GitHub Issues](https://github.com/majidershadi/vmware-vision/issues) for bugs and feature requests. Include the app and Splunk versions, the search app context, a sanitized event and the expected result. Do not include passwords, tokens or unredacted customer logs.

VMware Vision is an independent project and is not an official VMware, Broadcom or Splunk product.
