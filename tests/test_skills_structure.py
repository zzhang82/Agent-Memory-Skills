"""
Tests for skill structure, frontmatter, and file integrity.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class TestSkillStructure(unittest.TestCase):
    def setUp(self):
        self.skills_dir = ROOT / "skills"

    def test_skills_directories_exist(self):
        self.assertTrue((self.skills_dir / "amb").is_dir(), "skills/amb directory must exist")
        self.assertTrue((self.skills_dir / "amb-connect").is_dir(), "skills/amb-connect directory must exist")

    def test_amb_required_files(self):
        expected = [
            "SKILL.md",
            "references/tool_matrix.md",
            "references/everyday_workflows.md",
            "references/record_templates.md",
            "references/revision_and_correction.md",
            "references/scope_and_namespaces.md",
            "references/advanced_modes.md",
        ]
        for rel in expected:
            p = self.skills_dir / "amb" / rel
            self.assertTrue(p.is_file(), f"amb missing required file: {rel}")

    def test_amb_connect_required_files(self):
        expected = [
            "SKILL.md",
            "references/capability_discovery.md",
            "references/transports_and_auth.md",
            "references/local_stdio_recipe.md",
            "references/remote_http_recipe.md",
            "references/docker_deployment.md",
            "references/tool_profiles.md",
            "references/lifecycle_and_hooks.md",
            "references/verification_and_repair.md",
        ]
        for rel in expected:
            p = self.skills_dir / "amb-connect" / rel
            self.assertTrue(p.is_file(), f"amb-connect missing required file: {rel}")

    def test_frontmatter_presence(self):
        for skill in ["amb", "amb-connect"]:
            skill_md = self.skills_dir / skill / "SKILL.md"
            content = skill_md.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---"), f"{skill}/SKILL.md must start with frontmatter")
            parts = content.split("---", 2)
            self.assertGreaterEqual(len(parts), 3, f"{skill}/SKILL.md frontmatter must be closed")
            fm = parts[1]
            self.assertIn(f"name: {skill}", fm)
            self.assertIn("version:", fm)
            self.assertIn("description:", fm)

if __name__ == "__main__":
    unittest.main()
