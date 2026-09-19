#!/usr/bin/env python3
"""Splunk external lookup: no network, writes, credentials or external dependencies."""

import csv
import io
import sys
from vmware_vision_parser import OUTPUT_FIELDS, parse


def main():
    # Quote matching keys so Splunk retains their boundary whitespace.
    sys.stdin.reconfigure(newline="")
    sys.stdout.reconfigure(newline="")
    csv.field_size_limit(4 * 1024 * 1024)
    reader = csv.DictReader(sys.stdin)
    inputs = reader.fieldnames or ["_raw", "host", "sourcetype"]
    fields = list(dict.fromkeys(inputs + OUTPUT_FIELDS))
    keys = [name for name in ("_raw", "host", "sourcetype") if name in inputs]
    outputs = [name for name in fields if name not in keys]
    key_buffer = io.StringIO(newline="")
    key_writer = csv.writer(key_buffer, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(keys + outputs)
    for row in reader:
        try:
            row.update(
                parse(
                    row.get("_raw", ""), row.get("host", ""), row.get("sourcetype", "")
                )
            )
        except (ValueError, TypeError, RecursionError):
            row.update(dict.fromkeys(OUTPUT_FIELDS, ""))
            row["parser_status"] = "parse_error"
        key_buffer.seek(0)
        key_buffer.truncate()
        key_writer.writerow([row.get(name, "") for name in keys])
        sys.stdout.write(key_buffer.getvalue()[:-1] + ",")
        writer.writerow([row.get(name, "") for name in outputs])


if __name__ == "__main__":
    main()
