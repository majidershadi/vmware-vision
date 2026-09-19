"""The external lookup must return matching keys exactly, including whitespace."""
import csv
import io
from pathlib import Path
import subprocess
import sys
import unittest


class LookupCSV(unittest.TestCase):
    def test_keys_survive_csv_round_trip_and_are_always_quoted(self):
        base = "eventType=VmPoweredOnEvent vm_id=vm-1"
        messages = [base, base + " ", base + "\t", " " + base,
                    base + ', detail="quoted" ', base + "\nline two ",
                    base + "\r\nline two\r\n", base + " note=آزمایش "]
        source = io.StringIO(newline="")
        writer = csv.writer(source)
        writer.writerow(["_raw", "host", "sourcetype"])
        writer.writerows((raw, " vc01 ", "vmware:vision:vcenter") for raw in messages)
        script = Path(__file__).resolve().parents[1] / "package/bin/vmware_lookup.py"
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(script)],
            input=source.getvalue().encode("utf-8"), capture_output=True, check=True,
        )
        # Empty normalized outputs must remain unquoted so Splunk treats them as missing.
        self.assertIn(b",,", result.stdout)
        self.assertNotIn(b',"",', result.stdout)
        rows = list(csv.DictReader(io.StringIO(result.stdout.decode("utf-8"), newline="")))
        self.assertEqual(len(rows), len(messages))
        self.assertEqual(result.stderr, b"")
        for raw, row in zip(messages, rows):
            with self.subTest(raw=repr(raw)):
                self.assertEqual(row["_raw"], raw)
                self.assertEqual(row["host"], " vc01 ")
                self.assertEqual(row["sourcetype"], "vmware:vision:vcenter")
                self.assertEqual(row["record_kind"], "event")
                self.assertEqual(row["parser_status"], "mapped")
                self.assertTrue(row["parser_version"])
                quoted_key = '"' + raw.replace('"', '""') + '",'
                self.assertIn(quoted_key.encode("utf-8"), result.stdout)


if __name__ == "__main__":
    unittest.main()
