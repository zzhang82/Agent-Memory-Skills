"""
Negative mutation and regression tests for validator and contract enforcement.
Ensures that contract-breaking mutations are reliably caught by the actual validate_skills functions.
"""

import unittest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

# Import validator functions directly from scripts/validate_skills.py
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import validate_skills

class TestNegativeMutations(unittest.TestCase):
    def test_duplicate_tool_header_detected(self):
        matrix_file = ROOT / "skills" / "amb" / "references" / "tool_matrix.md"
        text = matrix_file.read_text(encoding="utf-8")
        corrupted = text + "\n### `store`\nDuplicate store section.\n"
        errors = validate_skills.check_tool_matrix_headings(text_override=corrupted)
        self.assertTrue(len(errors) > 0, "Duplicate header must trigger validator errors")
        self.assertTrue(any("duplicate" in err.lower() or "count" in err.lower() for err in errors))

    def test_trailing_hashes_duplicate_header_detected(self):
        matrix_file = ROOT / "skills" / "amb" / "references" / "tool_matrix.md"
        text = matrix_file.read_text(encoding="utf-8")
        corrupted = text + "\n### `store` ###\nDuplicate store section with trailing hashes.\n"
        errors = validate_skills.check_tool_matrix_headings(text_override=corrupted)
        self.assertTrue(len(errors) > 0, "Duplicate header with trailing hashes must trigger validator errors")
        self.assertTrue(any("duplicate" in err.lower() for err in errors))

    def test_18th_tool_in_public_order_detected(self):
        tp_file = ROOT / "skills" / "amb-connect" / "references" / "tool_profiles.md"
        text = tp_file.read_text(encoding="utf-8")
        
        # Test unindented 18th tool
        corrupted1 = text.replace("17. `ack_signal`", "17. `ack_signal`\n18. `invented_tool`")
        errors1 = validate_skills.check_public_tool_order(text_override=corrupted1)
        self.assertTrue(len(errors1) > 0, "Unindented 18th tool must trigger validator error")
        self.assertTrue(any("17 numbered entries" in err or "found 18" in err for err in errors1))

        # Test indented 18th tool
        corrupted2 = text.replace("17. `ack_signal`", "17. `ack_signal`\n  18. `invented_tool`")
        errors2 = validate_skills.check_public_tool_order(text_override=corrupted2)
        self.assertTrue(len(errors2) > 0, "Indented 18th tool must trigger validator error")
        self.assertTrue(any("17 numbered entries" in err or "found 18" in err for err in errors2))

    def test_broken_badge_link_detected(self):
        badge_snippet = '[![Badge](https://img.shields.io/badge/test)](NONEXISTENT_FILE.md)'
        targets = validate_skills.extract_markdown_link_targets(badge_snippet)
        self.assertIn("NONEXISTENT_FILE.md", targets, "Destination in badge link must be extracted")

    def test_noncanonical_numbering_detected(self):
        tp_file = ROOT / "skills" / "amb-connect" / "references" / "tool_profiles.md"
        text = tp_file.read_text(encoding="utf-8")
        corrupted = text.replace("17. `ack_signal`", "99. `ack_signal`")
        errors = validate_skills.check_public_tool_order(text_override=corrupted)
        self.assertTrue(len(errors) > 0, "Noncanonical number 99 must trigger validator error")
        self.assertTrue(any("noncanonical numbering" in err for err in errors))

    def test_reserved_tag_in_revise_rejected(self):
        bad_doc = 'revise(id="x", tags=["status:pinned", "domain:retrieval"])'
        match = re.search(r'revise\([^)]*tags=\[([^\]]+)\]', bad_doc, re.DOTALL)
        self.assertIsNotNone(match)
        assert match is not None
        tags_str = match.group(1)
        found = [p for p in validate_skills.RESERVED_TAG_PREFIXES if f'"{p}' in tags_str or f"'{p}'" in tags_str]
        self.assertIn("status:", found, "Reserved tag prefix 'status:' must be detected")

if __name__ == "__main__":
    unittest.main()
