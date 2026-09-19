# Changes

## VMware Vision 1.1.1

- Quote external lookup CSV output so leading and trailing whitespace no longer prevents matching results to events. Preserve input line endings and original raw text.
- Recognize explicit ESXi Hostd logout events without treating logout as a CIM login.
- Classify supported Envoy access, UI subscription retry and SPS debug messages as diagnostics. Keep unknown messages visible.
- Include numeric Hostd events in audit searches and show missing lookup output separately from unclassified traffic in coverage charts.
- Keep the ingestion TA at 1.0.2; no ingestion settings change. See the upgrade and validation guides for the remaining embedded-CRLF lookup limitation.

## VMware Vision 1.1.0

- Enable Splunkbase update checks in both package metadata and the UCC build settings; reject disabled checks during release verification.

- Add scoped CIM Authentication and Change mappings for explicit VMware events and outcomes.
- Preserve native operations in `vmware_action`. Eligible records now use CIM values in `action`; update custom searches and rebuild enabled model summaries when upgrading.
- Declare lookup-derived field values with `INDEXED_VALUE=false` so base-search filters and model constraints do not discard records before normalization.
- Keep the automatic lookup available outside the app through explicit script metadata.
- Declare Python 3.9 and 3.13, with a Python 3.9 fallback for earlier Splunk configuration handling.
- Add the eye-and-VM icon, a source build workflow, deployment guides and Apache 2.0 licensing.

The search app still normalizes syslog at search time. It does not poll VMware APIs, provide complete inventory, or establish that every requested operation completed.

## TA-vmware-vision 1.0.2

- Give the ingestion TA a distinct beacon-and-VM icon while retaining the app's eye-and-VM branding.
- Include a dedicated TA configuration guide with collector file inputs, forwarding checks and deployment acceptance steps.
- Keep raw parsing settings unchanged and update checks enabled. No reindexing or data-model rebuild is required for this TA update.

## TA-vmware-vision 1.0.1

- Enable Splunkbase update checks for upload validation.

- Publish under Apache 2.0, add the project icon and update deployment documentation for VMware Vision 1.1.0.
- Keep event boundaries, timestamp handling and encoding unchanged from 1.0.0. There is no search-time Python lookup in the TA.

## Earlier internal releases

Version 1.0.3 corrected cross-app visibility of the scripted lookup. Version 1.0.2 selected the Python 3.9 runtime. Version 1.0.1 separated diagnostics from event records and introduced the compact activity model. These releases preceded this public source distribution.
