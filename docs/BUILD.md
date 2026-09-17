# Build from source

The release follows the same sequence for both packages: build, verify, package, checksum and AppInspect. It uses UCC 6.6.0 directly and does not depend on a previous release archive.

## Requirements

- Linux or a Linux environment under WSL, with Bash, GNU Make and Git.
- Python 3.10 or newer for the build tools, including `venv` and `pip`.
- Network access to PyPI and the repositories used by UCC during its first build.
- Enough space for the virtual environment and generated UCC output.

The build environment is separate from Splunk's Python runtime. Do not install these development tools into `/opt/splunk`.

## 1. Clone and create the environment

```bash
git clone https://github.com/majidershadi/vmware-vision.git
cd vmware-vision
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
```

`requirements-build.txt` pins UCC and AppInspect. Their build-time transitive dependencies are resolved by pip. `package/lib/requirements.txt` separately pins and hashes the libraries shipped for the UCC configuration page. The syslog lookup itself uses Python's standard library only.

## 2. Run the source checks

```bash
make test
```

Checks cover parsing, event outcomes, CIM exclusions, preservation of native actions, dashboard queries, cross-app lookup visibility and separation of ingestion settings. The tests stay in the source repository; they are not installed with either package.

To test against a Splunk installation's bundled interpreters:

```bash
/opt/splunk/bin/splunk cmd python3.9 -m unittest discover -s tests -q
/opt/splunk/bin/splunk cmd python3.13 -m unittest discover -s tests -q
```

Run only the interpreter versions available in that installation. These unit tests do not log in, change settings or ingest events.

## 3. Build the app

```bash
make build
```

The source check compares the app, parser and manifest versions and verifies the lookup output contract. UCC builds `output/vmware_vision`, installs the pinned runtime dependencies and creates its configuration UI. The post-build hook restores app navigation, declares both Python runtimes, includes the administrator documentation and removes bytecode caches. The verifier checks the result before it can be packaged.

The build will fail if native binaries, local settings, test directories, private keys or invalid icon dimensions appear in the app. Third-party license files and the UCC runtime bootstrap are retained.

## 4. Create installation archives

```bash
make package
```

Expected files:

```text
dist/vmware_vision-1.1.0.tar.gz
dist/TA-vmware-vision-1.0.1.tar.gz
dist/SHA256SUMS.txt
```

The TA is built from the full app's raw parsing settings using an explicit file list. It contains no Python scripts, search-time lookups, dashboards or enabled inputs.

Check downloaded or copied archives with:

```bash
cd dist
sha256sum -c SHA256SUMS.txt
```

## 5. Run AppInspect

```bash
make appinspect
```

Or build and inspect in one command:

```bash
make release
```

Each archive gets an AppInspect JSON report and native exit-code file in `dist/`. The release gate stops on errors, failures or future failures. Warnings remain in the report for review; they are not silently removed. A successful local gate does not submit to Splunkbase or replace its review.

UCC may embed a build timestamp, so independent full app builds are not promised to have identical bytes. Checksums identify the exact released archives. The ingestion TA archive uses deterministic member ordering, timestamps and permissions.

## Source layout

| Path | Edit here for |
|---|---|
| `package/bin/vmware_vision_parser.py` | Source formats, identities, event classification and VMware actions |
| `package/bin/vmware_vision_cim.py` | CIM allowlists and field mappings |
| `package/bin/vmware_lookup.py` | Splunk CSV lookup interface |
| `package/default/` | Search settings, models, dashboards, macros and reports |
| `package/metadata/default.meta` | Cross-app knowledge-object visibility |
| `package/static/` | Launcher icons and app branding |
| `package/appserver/static/` | Web assets and dashboard styling |
| `globalConfig.json` | UCC configuration page |
| `additional_packaging.py` | Small changes to UCC output |
| `tools/build_ta.py` | Ingestion-only package contents |
| `docs/` | Administrator and developer documentation |

Do not edit `output/` as the lasting source of a change. The next build replaces generated output. The checked-in files under `package/` are the source of truth.

## Changing a version or field

Before a release, update the app version in `Makefile`, `globalConfig.json`, `package/app.manifest`, `package/default/app.conf`, the parser's `VERSION` and `package/README.txt`. Update the TA version in `Makefile` and `tools/build_ta.py` only when that package changes.

When adding a lookup field, update `OUTPUT_FIELDS`, the props output list, transform command/field list and any model that exposes it. Add `INDEXED_VALUE=false` when its value is computed and may not exist literally in the raw log. Keep compatibility notes and examples in step with field changes. The source verifier catches mismatched lookup output lists.

Build in a fresh checkout before publishing. Keep release archives, reports and environment files out of Git; attach the selected release artifacts to the GitHub release. Never include lab credentials, collected customer events or local Splunk configuration.
