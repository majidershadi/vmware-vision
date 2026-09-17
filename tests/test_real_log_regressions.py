"""Sanitized regression shapes from relayed vCenter diagnostic samples."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "package/bin"))
from vmware_vision_parser import parse
from test_parser import event


def diagnostic(body, app="vpxd-main"):
    return (
        "Sep 16 10:35:14 192.0.2.50 1 2026-09-16T07:05:15.540951+00:00 "
        "vc01.example " + app + " - - - 2026-09-16T07:05:15.540Z info "
        "vpxd[11241] [Originator@6876 sub=MoCluster opID=example] " + body
    )


class RealLogRegressions(unittest.TestCase):
    def test_service_principal_is_not_event_type(self):
        result = parse(
            diagnostic(
                "Trying to get current VC connection; user: com.vmware.vim.eam",
                "vum-vmacore",
            ),
            "relay",
        )
        self.assertEqual(result["event_type"], "")
        self.assertEqual(result["parser_status"], "diagnostic")
        self.assertEqual(result["action"], "diagnostic_message")
        self.assertEqual(result["vcenter"], "vc01.example")
        self.assertEqual(result["component"], "vum-vmacore")

    def test_multivm_diagnostic_has_no_arbitrary_primary_vm(self):
        result = parse(
            diagnostic(
                "Dumping vCLS host infos [{vm: [vim.VirtualMachine:vm-101,vCLS-a]}, {vm: [vim.VirtualMachine:vm-102,vCLS-b]}]"
            )
        )
        self.assertEqual(result["vm_reference_count"], "2")
        for name in ["vm_key", "vm_id", "vm_name", "observed_state"]:
            self.assertEqual(result[name], "", name)
        self.assertEqual(result["record_kind"], "diagnostic")

    def test_single_reference_retains_name_but_is_not_change(self):
        result = parse(
            diagnostic(
                "For VM [vim.VirtualMachine:vm-103,Finance VDI 01], LB overhead limit (130) is less than overhead (144)."
            )
        )
        self.assertEqual(
            (result["vm_name"], result["vm_id"]), ("Finance VDI 01", "vm-103")
        )
        self.assertEqual(result["record_kind"], "diagnostic")
        self.assertEqual(result["category"], "diagnostic")
        self.assertEqual(result["observed_state"], "")

    def test_internal_query_and_finish_are_not_lifecycle(self):
        for body in [
            "[VpxLRO] -- BEGIN lro-133 -- ResourceModel -- vim.dp.ResourceModel.queryBatch -- abc",
            "[VpxLRO] -- FINISH lro-133",
        ]:
            result = parse(diagnostic(body))
            self.assertEqual(result["event_type"], "")
            self.assertEqual(result["record_kind"], "diagnostic")

    def test_relay_wrapped_lifecycle_retains_original_source(self):
        raw = (
            "Sep 16 10:35:14 192.0.2.50 "
            + event("VmPoweredOnEvent", "Virtual machine app01 is powered on")[4:]
        )
        result = parse(raw, "relay")
        self.assertEqual(result["vcenter"], "vc01.example")
        self.assertEqual(result["record_kind"], "event")
        self.assertEqual(result["observed_state"], "powered_on")

    def test_alarm_extracts_host_and_transition_without_vm(self):
        result = parse(
            event(
                "AlarmStatusChangedEvent",
                "Alarm 'Host connection and power state' on 192.0.2.110 changed from Red to Green",
            )
        )
        self.assertEqual(result["esxi_host"], "192.0.2.110")
        self.assertEqual((result["old_value"], result["new_value"]), ("Red", "Green"))
        self.assertEqual(result["status"], "observed")
        self.assertEqual(result["vm_key"], "")

    def test_host_connection_is_not_a_vm_identity(self):
        result = parse(
            event("HostConnectedEvent", "Connected to 192.0.2.110 in ExampleDC")
        )
        self.assertEqual(result["esxi_host"], "192.0.2.110")
        self.assertEqual(result["vm_key"], "")
        self.assertEqual(result["action"], "host_connection_changed")

    def test_generic_json_type_is_not_event_class(self):
        result = parse('{"type":"syslog", "message":"Routine service message"}')
        self.assertEqual(result["event_type"], "")
        self.assertEqual(result["record_kind"], "unclassified")

    def test_unrecognized_event_class_still_visible(self):
        result = parse(event("VendorFutureEvent", "Unsupported event class"))
        self.assertEqual(result["record_kind"], "event")
        self.assertEqual(result["parser_status"], "unmapped_event_type")

    def test_explicit_vm_identity_precedes_diagnostic_references(self):
        result = parse(
            diagnostic(
                'vm_id=vm-201 vm_name="Primary VM" references [vim.VirtualMachine:vm-101,Other]'
            )
        )
        self.assertEqual((result["vm_id"], result["vm_name"]), ("vm-201", "Primary VM"))


if __name__ == "__main__":
    unittest.main()
