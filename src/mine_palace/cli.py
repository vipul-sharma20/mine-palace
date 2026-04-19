from __future__ import annotations

import argparse
import os
from pathlib import Path

from .planner import build_world_plan
from .render import WorldRenderer
from .rcon import RconClient
from .sample import write_sample_vault
from .vault import parse_vault


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Minecraft memory palace from an Obsidian vault.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample_parser = subparsers.add_parser("sample-vault", help="Write the bundled sample vault to disk.")
    sample_parser.add_argument("destination", type=Path, help="Directory to write the sample vault into.")
    sample_parser.set_defaults(func=cmd_sample_vault)

    plan_parser = subparsers.add_parser("plan", help="Parse a vault and generate world build artifacts.")
    _add_plan_args(plan_parser)
    plan_parser.set_defaults(func=cmd_plan)

    demo_parser = subparsers.add_parser("demo", help="Generate a demo build from the bundled sample vault.")
    demo_parser.add_argument("--output", type=Path, required=True, help="Directory for generated build artifacts.")
    demo_parser.add_argument("--origin-x", type=int, default=0)
    demo_parser.add_argument("--origin-y", type=int, default=64)
    demo_parser.add_argument("--origin-z", type=int, default=0)
    demo_parser.add_argument("--limit", type=int, default=24)
    demo_parser.set_defaults(func=cmd_demo)

    apply_parser = subparsers.add_parser("apply-rcon", help="Replay generated commands against a server over RCON.")
    apply_parser.add_argument("--commands", type=Path, required=True, help="Path to the build command file.")
    apply_parser.add_argument("--host", default="127.0.0.1")
    apply_parser.add_argument("--port", type=int, default=25575)
    apply_parser.add_argument("--password", help="RCON password. Falls back to MC_RCON_PASSWORD.")
    apply_parser.add_argument("--rate-limit-ms", type=int, default=0)
    apply_parser.add_argument("--progress-every", type=int, default=25)
    apply_parser.set_defaults(func=cmd_apply_rcon)

    return parser


def _add_plan_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--vault", type=Path, required=True, help="Vault root to parse.")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for generated artifacts.")
    parser.add_argument("--name", default="Mine Palace", help="World name used in metadata.")
    parser.add_argument("--limit", type=int, help="Maximum number of notes to include.")
    parser.add_argument("--include", nargs="*", help="Top-level folders to include.")
    parser.add_argument("--origin-x", type=int, default=0)
    parser.add_argument("--origin-y", type=int, default=64)
    parser.add_argument("--origin-z", type=int, default=0)
    parser.add_argument("--no-books", action="store_true", help="Skip experimental written-book commands.")


def cmd_sample_vault(args: argparse.Namespace) -> int:
    destination = write_sample_vault(args.destination)
    print(f"Sample vault written to {destination}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    return _plan_from_vault(
        vault=args.vault,
        output=args.output,
        name=args.name,
        limit=args.limit,
        include=args.include,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        include_books=not args.no_books,
    )


def cmd_demo(args: argparse.Namespace) -> int:
    sample_root = args.output / "sample_vault"
    write_sample_vault(sample_root)
    return _plan_from_vault(
        vault=sample_root,
        output=args.output,
        name="Mine Palace Demo",
        limit=args.limit,
        include=None,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        origin_z=args.origin_z,
        include_books=True,
    )


def _plan_from_vault(
    *,
    vault: Path,
    output: Path,
    name: str,
    limit: int | None,
    include: list[str] | None,
    origin_x: int,
    origin_y: int,
    origin_z: int,
    include_books: bool,
) -> int:
    notes = parse_vault(vault, limit=limit, include_districts=include)
    if not notes:
        raise SystemExit("No notes found after parsing. Check your path or include filters.")

    plan = build_world_plan(
        notes,
        name=name,
        source_vault=vault,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
    )
    renderer = WorldRenderer()
    outputs = renderer.render(plan, output, include_books=include_books)

    print(f"World plan: {plan.name}")
    print(f"Source vault: {vault}")
    print(f"Districts: {len(plan.districts)}")
    print(f"Notes: {plan.note_count}")
    print("Artifacts:")
    for label, path in outputs.items():
        print(f"  {label}: {path}")

    return 0


def cmd_apply_rcon(args: argparse.Namespace) -> int:
    password = args.password or os.environ.get("MC_RCON_PASSWORD")
    if not password:
        raise SystemExit("Missing RCON password. Provide --password or set MC_RCON_PASSWORD.")

    commands = [
        line.strip()
        for line in args.commands.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    with RconClient(args.host, args.port, password) as client:
        client.command_many(
            commands,
            rate_limit_ms=args.rate_limit_ms,
            progress_every=args.progress_every,
        )

    print(f"Applied commands from {args.commands}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
