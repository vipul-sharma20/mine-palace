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

    deploy_parser = subparsers.add_parser(
        "deploy-rcon",
        help="Apply clear/build/books phases from a generated artifact directory over RCON.",
    )
    deploy_parser.add_argument(
        "--artifacts",
        type=Path,
        required=True,
        help="Generated output directory that contains commands/*.txt files.",
    )
    deploy_parser.add_argument("--host", default="127.0.0.1")
    deploy_parser.add_argument("--port", type=int, default=25575)
    deploy_parser.add_argument("--password", help="RCON password. Falls back to MC_RCON_PASSWORD.")
    deploy_parser.add_argument("--rate-limit-ms", type=int, default=0)
    deploy_parser.add_argument("--progress-every", type=int, default=25)
    deploy_parser.add_argument("--skip-clear", action="store_true", help="Skip clear.txt before building.")
    deploy_parser.add_argument("--skip-books", action="store_true", help="Skip optional books.txt phase.")
    deploy_parser.set_defaults(func=cmd_deploy_rcon)

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
    password = _resolve_rcon_password(args.password)
    commands = _read_commands(args.commands)

    with RconClient(args.host, args.port, password) as client:
        client.command_many(
            commands,
            rate_limit_ms=args.rate_limit_ms,
            progress_every=args.progress_every,
        )

    print(f"Applied commands from {args.commands}")
    return 0


def cmd_deploy_rcon(args: argparse.Namespace) -> int:
    password = _resolve_rcon_password(args.password)
    phases = _command_batches_from_artifacts(
        args.artifacts,
        skip_clear=args.skip_clear,
        skip_books=args.skip_books,
    )

    with RconClient(args.host, args.port, password) as client:
        for label, path, commands in phases:
            print(f"Applying {label} from {path}")
            client.command_many(
                commands,
                rate_limit_ms=args.rate_limit_ms,
                progress_every=args.progress_every,
            )

    print(f"Deployment complete from {args.artifacts}")
    return 0


def _resolve_rcon_password(cli_password: str | None) -> str:
    password = cli_password or os.environ.get("MC_RCON_PASSWORD")
    if not password:
        raise SystemExit("Missing RCON password. Provide --password or set MC_RCON_PASSWORD.")
    return password


def _command_batches_from_artifacts(
    artifacts_dir: Path,
    *,
    skip_clear: bool,
    skip_books: bool,
) -> list[tuple[str, Path, list[str]]]:
    commands_dir = artifacts_dir / "commands"
    phases: list[tuple[str, Path, list[str]]] = []

    if not skip_clear:
        clear_path = commands_dir / "clear.txt"
        phases.append(("clear", clear_path, _read_commands(clear_path)))

    build_path = commands_dir / "build.txt"
    phases.append(("build", build_path, _read_commands(build_path)))

    if not skip_books:
        books_path = commands_dir / "books.txt"
        book_commands = _read_commands(books_path, required=False)
        if book_commands:
            phases.append(("books", books_path, book_commands))

    return phases


def _read_commands(path: Path, *, required: bool = True) -> list[str]:
    if not path.exists():
        if required:
            raise SystemExit(f"Missing command file: {path}")
        return []

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
