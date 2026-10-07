"""
Tests for technical contracts, 17 MCP tools, profiles, and AMB v0.36 invariants.
"""

import unittest
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class TestContracts(unittest.TestCase):
    def setUp(self):
        self.skills_dir = ROOT / "skills"

    def test_all_17_tools_in_amb_matrix(self):
        matrix_file = self.skills_dir / "amb" / "references" / "tool_matrix.md"
        content = matrix_file.read_text(encoding="utf-8")
        
        all_17_tools = [
            "store", "recall", "browse", "stats",
            "forget", "feedback", "promote", "annotate", "revise", "export",
            "begin_run", "record_run_event", "get_run", "complete_run",
            "claim_signal", "extend_signal_lease", "ack_signal"
        ]
        
        for tool in all_17_tools:
            self.assertTrue(
                f"### `{tool}`" in content,
                f"Tool '{tool}' must have an explicit '### `{tool}`' section in tool_matrix.md"
            )

    def test_everyday_profile_consistency_across_files(self):
        everyday_6 = {"recall", "browse", "stats", "store", "revise", "annotate"}
        
        # 1. amb/SKILL.md
        amb_skill = (self.skills_dir / "amb" / "SKILL.md").read_text(encoding="utf-8")
        for tool in everyday_6:
            self.assertIn(f"`{tool}`", amb_skill)

        # 2. amb-connect/references/tool_profiles.md table
        tp_text = (self.skills_dir / "amb-connect" / "references" / "tool_profiles.md").read_text(encoding="utf-8")
        match = re.search(r'\|\s*Everyday\s*\(6\)\s*\|\s*([^|]+)\|', tp_text)
        self.assertIsNotNone(match, "Everyday (6) row must exist in tool_profiles.md table")
        assert match is not None
        table_tools = set(re.findall(r'`(\w+)`', match.group(1)))
        self.assertEqual(table_tools, everyday_6, "tool_profiles.md Everyday table must match Everyday 6")

        # 3. amb-connect/references/tool_profiles.md JSON snippet
        json_match = re.search(r'"enabledTools"\s*:\s*\[(.*?)\]', tp_text, re.DOTALL)
        self.assertIsNotNone(json_match, "enabledTools JSON snippet must exist in tool_profiles.md")
        assert json_match is not None
        json_tools = set(re.findall(r'"(\w+)"', json_match.group(1)))
        self.assertEqual(json_tools, everyday_6, "tool_profiles.md enabledTools JSON must match Everyday 6")

        # 4. amb-connect/references/verification_and_repair.md
        vr_text = (self.skills_dir / "amb-connect" / "references" / "verification_and_repair.md").read_text(encoding="utf-8")
        vr_match = re.search(r'Everyday expects\s+([^.\n]+)', vr_text)
        self.assertIsNotNone(vr_match, "verification_and_repair.md must state what Everyday expects")
        assert vr_match is not None
        vr_tools = set(re.findall(r'`(\w+)`', vr_match.group(1)))
        self.assertEqual(vr_tools, everyday_6, "verification_and_repair.md Everyday list must match Everyday 6")

    def test_redlines_in_amb(self):
        amb_skill = (self.skills_dir / "amb" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Redlines", amb_skill)
        self.assertTrue(
            "transcript" in amb_skill.lower() or "chat history" in amb_skill.lower(),
            "amb must forbid raw transcript dumping"
        )
        self.assertTrue(
            "signal-only" in amb_skill.lower() or "signal_status" in amb_skill.lower(),
            "amb must warn against passing signal parameters to memory tools"
        )

    def test_policy_tag_isolation_in_revision(self):
        rev_text = (self.skills_dir / "amb" / "references" / "revision_and_correction.md").read_text(encoding="utf-8")
        self.assertNotIn('tags=["kind:', rev_text, "revised example must not pass kind: in caller tags")
        self.assertIn("reserved", rev_text.lower(), "must document reserved policy tag isolation")

    def test_governed_run_requirements_documented(self):
        adv_text = (self.skills_dir / "amb" / "references" / "advanced_modes.md").read_text(encoding="utf-8")
        self.assertIn("acceptance_criteria", adv_text)
        self.assertIn("expected_database_epoch", adv_text)
        self.assertIn("expected_run_generation", adv_text)
        self.assertIn("expected_last_sequence", adv_text)
        self.assertIn("verification_receipt_id", adv_text)

    def test_redlines_in_amb_connect(self):
        connect_skill = (self.skills_dir / "amb-connect" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Redlines", connect_skill)
        self.assertTrue(
            "fail closed" in connect_skill.lower(),
            "amb-connect must mandate failing closed on remote authority error"
        )
        self.assertTrue(
            "remote write-side capture" in connect_skill.lower(),
            "amb-connect must document that write-side candidate capture is local-only"
        )

    def test_transports_documented(self):
        transports_doc = (self.skills_dir / "amb-connect" / "references" / "transports_and_auth.md").read_text(encoding="utf-8")
        self.assertIn("stdio", transports_doc)
        self.assertIn("Streamable HTTP", transports_doc)
        self.assertIn("AGENT_MEMORY_BRIDGE_HOME", transports_doc)
        self.assertIn("AGENT_MEMORY_BRIDGE_HTTP_TOKEN_FILE", transports_doc)

if __name__ == "__main__":
    unittest.main()
