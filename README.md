# Mine Palace

Mine Palace turns an Obsidian-style markdown vault into a walkable Minecraft memory palace.

This implementation is intentionally hackathon-shaped:

- no external Python dependencies
- deterministic sample vault for demos
- world planning based on folders and notes
- output as `mcfunction` files, plain command lists, and a visual HTML preview
- optional live application over RCON

## What it builds

- a central hub
- one district per top-level folder
- note alcoves laid out inside each district
- paths from the hub to each district
- signs, shelves, lecterns, and barrels for each note
- optional experimental book placement commands

## Quick Start

Generate a demo world from the bundled sample vault:

```bash
cd /Users/vipul/projects/mine-palace
PYTHONPATH=src python3 -m mine_palace.cli demo --output build/demo
```

Build from a real vault:

```bash
cd /Users/vipul/projects/mine-palace
PYTHONPATH=src python3 -m mine_palace.cli plan \
  --vault /Users/vipul/tools/noto \
  --output build/noto \
  --limit 60
```

If you want to bias the build toward specific folders:

```bash
PYTHONPATH=src python3 -m mine_palace.cli plan \
  --vault /Users/vipul/tools/noto \
  --output build/curated \
  --include Engineering Incidents LLM Meetings Projects Self
```

Apply the generated structure commands to a running Minecraft server over RCON:

```bash
export MC_RCON_PASSWORD='...'
PYTHONPATH=src python3 -m mine_palace.cli apply-rcon \
  --commands build/demo/commands/clear.txt \
  --host 127.0.0.1 \
  --port 25575

PYTHONPATH=src python3 -m mine_palace.cli apply-rcon \
  --commands build/demo/commands/build.txt \
  --host 127.0.0.1 \
  --port 25575
```

## Output Structure

Running `plan` or `demo` generates:

- `manifest.json`: structured world plan
- `commands/clear.txt`: clear-and-reset commands for quick rebuilds
- `commands/build.txt`: plain commands, safe for RCON replay
- `commands/books.txt`: experimental written-book commands
- `mcfunction/clear.mcfunction`: clear function file
- `mcfunction/build.mcfunction`: structure build file
- `mcfunction/books.mcfunction`: optional book placement function
- `preview/index.html`: visual preview of the world layout

## Demo Flow

1. Run `demo` to generate a sample vault and world artifacts.
2. Open `preview/index.html` to inspect the plan.
3. Apply `commands/build.txt` over RCON to your test server.
4. Record a flythrough from hub to district to note alcove.

## Notes

- The structure build is the reliable path.
- Written-book placement is generated separately because command syntax can vary between server versions.
- For large vaults, the CLI uses balanced round-robin sampling so one folder does not dominate the demo.
