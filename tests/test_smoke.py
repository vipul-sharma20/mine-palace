from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mine_palace.cli import build_parser
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

    def test_deploy_rcon_replays_clear_build_and_books_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir) / "build"
            commands_dir = artifacts / "commands"
            commands_dir.mkdir(parents=True)
            (commands_dir / "clear.txt").write_text("# clear\nfill 0 0 0 1 1 1 air\n", encoding="utf-8")
            (commands_dir / "build.txt").write_text("# build\nsetblock 0 64 0 stone\n", encoding="utf-8")
            (commands_dir / "books.txt").write_text("# books\nsetblock 0 65 0 barrel\n", encoding="utf-8")

            parser = build_parser()
            args = parser.parse_args(
                [
                    "deploy-rcon",
                    "--artifacts",
                    str(artifacts),
                    "--password",
                    "secret",
                    "--host",
                    "mc.example.test",
                    "--port",
                    "25575",
                ]
            )

            fake_client = _FakeRconClient
            fake_client.instances.clear()
            with patch("mine_palace.cli.RconClient", fake_client):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = args.func(args)

        self.assertEqual(result, 0)
        self.assertEqual(len(fake_client.instances), 1)
        client = fake_client.instances[0]
        self.assertEqual(client.host, "mc.example.test")
        self.assertEqual(client.port, 25575)
        self.assertEqual(client.password, "secret")
        self.assertEqual(
            client.calls,
            [
                ["# clear", "fill 0 0 0 1 1 1 air"],
                ["# build", "setblock 0 64 0 stone"],
                ["# books", "setblock 0 65 0 barrel"],
            ],
        )

    def test_deploy_rcon_skips_missing_or_empty_books_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = Path(tmpdir) / "build"
            commands_dir = artifacts / "commands"
            commands_dir.mkdir(parents=True)
            (commands_dir / "clear.txt").write_text("fill 0 0 0 1 1 1 air\n", encoding="utf-8")
            (commands_dir / "build.txt").write_text("setblock 0 64 0 stone\n", encoding="utf-8")

            parser = build_parser()
            args = parser.parse_args(
                ["deploy-rcon", "--artifacts", str(artifacts), "--password", "secret"]
            )

            fake_client = _FakeRconClient
            fake_client.instances.clear()
            with patch("mine_palace.cli.RconClient", fake_client):
                with contextlib.redirect_stdout(io.StringIO()):
                    result = args.func(args)

        self.assertEqual(result, 0)
        self.assertEqual(len(fake_client.instances), 1)
        self.assertEqual(
            fake_client.instances[0].calls,
            [
                ["fill 0 0 0 1 1 1 air"],
                ["setblock 0 64 0 stone"],
            ],
        )


class _FakeRconClient:
    instances: list["_FakeRconClient"] = []

    def __init__(self, host: str, port: int, password: str, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.calls: list[list[str]] = []

    def __enter__(self) -> "_FakeRconClient":
        self.instances.append(self)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def command_many(
        self,
        commands: list[str],
        *,
        rate_limit_ms: int = 0,
        progress_every: int = 25,
    ) -> None:
        self.calls.append(commands)


if __name__ == "__main__":
    unittest.main()
