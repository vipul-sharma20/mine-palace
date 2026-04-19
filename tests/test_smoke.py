from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mine_palace.planner import build_world_plan
from mine_palace.render import WorldRenderer
from mine_palace.sample import write_sample_vault
from mine_palace.vault import parse_vault


class SmokeTests(unittest.TestCase):
    def test_sample_vault_parses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = write_sample_vault(Path(tmpdir) / "vault")
            notes = parse_vault(vault)

        self.assertGreaterEqual(len(notes), 8)
        self.assertIn("Projects", {note.district for note in notes})
        self.assertIn("Incidents", {note.district for note in notes})

    def test_render_outputs_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            vault = write_sample_vault(root / "vault")
            notes = parse_vault(vault, limit=8)
            plan = build_world_plan(notes, name="Test Palace", source_vault=vault)
            renderer = WorldRenderer()
            outputs = renderer.render(plan, root / "build")

            self.assertTrue(outputs["manifest"].exists())
            self.assertTrue(outputs["clear_commands"].exists())
            self.assertTrue(outputs["build_commands"].exists())
            self.assertTrue(outputs["preview"].exists())

    def test_index_note_is_deprioritized_when_limited(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            (vault / "Projects").mkdir(parents=True)
            (vault / "Projects" / "index.md").write_text("# Index\n\n- [[real-note]]\n", encoding="utf-8")
            (vault / "Projects" / "real-note.md").write_text(
                "# Real Note\n\nThis is the actual content we want in the world.\n\n[[index]] [[other]]\n",
                encoding="utf-8",
            )
            notes = parse_vault(vault, limit=1)

        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].path.name, "real-note.md")


if __name__ == "__main__":
    unittest.main()
