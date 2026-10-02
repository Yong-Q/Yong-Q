import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("profile_generator", ROOT / "scripts/update_profile.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.config = json.loads((ROOT / "profile.json").read_text())

    def repo(self, name, **changes):
        return dict(name=name, html_url=f"https://github.com/Yong-Q/{name}", fork=False,
                    private=False, archived=False, size=20, pushed_at="2026-10-01T00:00:00Z",
                    description="Research & computation <example>", language="Python", **changes)

    def test_new_public_project_appears_and_forks_private_archived_do_not(self):
        rows = [self.repo("New-research"), self.repo("Yong-Q")]
        for field in ["fork", "private", "archived"]:
            row = self.repo(field)
            row[field] = True
            rows.append(row)
        model = self.module.build_model(self.config, rows)
        self.assertEqual([r["name"] for r in model["recent"]], ["New-research"])

    def test_removed_featured_project_is_not_advertised(self):
        model = self.module.build_model(self.config, [self.repo("Sep-Pilot")])
        self.assertEqual([r["name"] for r in model["featured"]], ["Sep-Pilot"])

    def test_svg_escapes_untrusted_text_and_is_accessible(self):
        model = self.module.build_model(self.config, [self.repo("Sep-Pilot")])
        svg = self.module.render_svg(model)
        root = ET.fromstring(svg)
        self.assertIn("&lt;example&gt;", svg)
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
        self.assertNotIn("Alex", svg)

    def test_readme_preserves_user_content_outside_markers(self):
        model = self.module.build_model(self.config, [])
        original = "My notes\n<!-- PROFILE:START -->\nold\n<!-- PROFILE:END -->\nContact me\n"
        result = self.module.render_readme(model, original)
        self.assertTrue(result.startswith("My notes\n"))
        self.assertTrue(result.endswith("\nContact me\n"))

    def test_readme_handles_table_delimiters_and_newlines(self):
        row = self.repo("New-research")
        row["description"] = "a | b\n<script>alert(1)</script>"
        result = self.module.render_readme(self.module.build_model(self.config, [row]), "")
        self.assertIn("a &#124; b", result)
        self.assertNotIn("<script>", result)

    def test_api_failure_preserves_previous_results(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "profile.json").write_text(json.dumps(self.config))
            (path / "README.md").write_text("previous good result")
            with patch.object(self.module, "fetch_repos", side_effect=RuntimeError("API unavailable")):
                with self.assertRaises(RuntimeError):
                    self.module.generate(path)
            self.assertEqual((path / "README.md").read_text(), "previous good result")
            self.assertFalse((path / "data/profile.json").exists())


if __name__ == "__main__":
    unittest.main()
