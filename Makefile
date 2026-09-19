PYTHON ?= .venv/bin/python
UCC := .venv/bin/ucc-gen
APPINSPECT := .venv/bin/splunk-appinspect
VERSION := 1.1.1
TA_VERSION := 1.0.2

.PHONY: help test build verify package appinspect release

help:
	@printf '%s\n' 'make test        Run parser and configuration checks' 'make build       Build the app with UCC' 'make package     Build and verify both install packages' 'make appinspect  Inspect existing packages' 'make release     Build, package and inspect both packages'

test:
	$(PYTHON) -m unittest discover -s tests -q

build: test
	$(PYTHON) tools/verify_source.py $(VERSION)
	$(UCC) build --source package --config globalConfig.json --ta-version $(VERSION) --python-binary-name "$(abspath $(PYTHON))" --overwrite
	$(PYTHON) tools/verify_release.py output/vmware_vision $(VERSION)

verify:
	$(PYTHON) tools/verify_release.py output/vmware_vision $(VERSION)

package: build
	mkdir -p dist
	$(UCC) package --path output/vmware_vision --output dist
	$(PYTHON) tools/build_ta.py
	$(PYTHON) tools/verify_release.py dist/vmware_vision-$(VERSION).tar.gz $(VERSION)
	$(PYTHON) tools/checksums.py

appinspect:
	$(PYTHON) tools/inspect_release.py $(APPINSPECT) dist/vmware_vision-$(VERSION).tar.gz dist/TA-vmware-vision-$(TA_VERSION).tar.gz

release: package appinspect
