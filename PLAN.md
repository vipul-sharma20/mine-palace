# Mine Palace Plan

## Canonical Idea

Mine Palace turns an Obsidian vault into a walkable Minecraft memory palace you can explore and share.

This is the core framing to hold onto.

- not a static library UI
- not a literal graph view
- not a diary-only product
- not just bookshelves as the idea

The headline is the transformation of notes into place.

## Product Thesis

The strongest version of the project is:

1. a real Minecraft world, not a mockup
2. a world with meaningful regions, not a flat warehouse of notes
3. a public-safe demo based on a curated engineer vault
4. one clear shareable artifact: a screenshot, overhead map, or short flythrough

Bookshelves, lecterns, signs, and barrels are mechanics inside the world. They are not the product framing.

## What To Build

Build a curated memory palace.

World structure:

- central hub: the mind / spawn / entry plaza
- districts: top-level folders or themes
- note alcoves: one note per shelf/lectern area
- related-note paths: a small number of visible connections between linked notes
- hidden paths: optional treatment for orphan or special notes

Recommended public demo districts:

- Projects
- Incidents
- Meetings
- LLM
- Career
- People

These are broad enough to be legible and specific enough to feel personal to engineers.

## What Not To Build

Do not spend hackathon time on:

- full-vault exhaustive import
- graph view as the visible metaphor
- live sync with Obsidian
- plugin/mod as the core product
- raw world-file editing as the main path
- multiplayer features
- auth, dashboards, search, profiles, payments
- semantic clustering or embeddings before the basic world is compelling

## Why This Plan Wins

Compared to the alternatives:

- pure library: too much storage metaphor, not enough payoff
- literal graph world: clever but emotionally flat and harder to read fast
- generic dungeon with no semantic mapping: dramatic but less meaningful

Memory palace is the right middle:

- visually legible
- emotionally resonant
- easy to explain in one sentence
- strong for a short demo clip

## Current Repo Direction

The repo direction is broadly correct already.

It should stay focused on these layers:

1. vault parser
2. world planner
3. renderer for commands and previews
4. live application to the test server

What should change is emphasis.

The next work should optimize for demo quality and clarity, not for breadth or generality.

## World Translation Rules

Use simple, deterministic mappings.

- top-level folder -> district
- note -> alcove or room
- note importance -> placement prominence or room size
- wiki links -> side paths, portals, or secret passages
- tags -> secondary labels or accent metadata
- long note body -> readable book or truncated excerpt in-world

The user should feel like they are walking through a world, not browsing a file system.

## Build Order

### Phase 0: Working Scaffold

Goal: prove the project can parse a vault and emit build artifacts.

Expected outputs:

- manifest.json
- build commands
- clear commands
- preview page
- sample vault

This phase is already the right foundation.

### Phase 1: Demo-Quality World

Goal: make the world visually legible and screenshot-worthy.

Tasks:

- strengthen the hub so the spawn shot looks intentional
- give each district a clearer entrance and stronger palette identity
- make note alcoves easier to read in-world
- add a small number of link-based paths so the world feels alive
- tune scale so the walk feels compact and demo-friendly

### Phase 2: Live Server Loop

Goal: make rebuilds on the deployed Minecraft server fast and repeatable.

Tasks:

- generate artifacts from the curated sample vault
- apply them to the test server over RCON
- reserve a stable build area for iteration
- verify readable notes on the actual server version
- rehearse a 20-30 second flythrough

### Phase 3: Public Demo Shell

Goal: turn the build into something people can understand and act on.

Tasks:

- lightweight landing page
- clear headline and one-line explanation
- sample world screenshots or flythrough embed
- one meaningful action: upload vault later, generate sample world, or join waitlist

### Phase 4: Stretch

Only after the demo feels strong:

- better link-based world layout
- private diary mode positioning
- more dramatic biomes or architecture styles
- selective import controls

## Immediate Priorities

The next highest-value tasks are:

1. curate the sample engineer vault to 30-50 strong notes across 5-6 districts
2. improve the renderer so the hub and district entrances look intentional in screenshots
3. deploy the sample world to the live server and iterate based on how it actually feels to walk
4. add 2-3 link-based secret paths or side routes
5. prepare the flythrough and landing page copy

Do not chase more parser features before the sample world is compelling.

## Demo Story

The demo should be simple.

1. Spawn in the hub.
2. Show the district signposts and overall layout.
3. Walk into one district.
4. Open a note alcove and show that it maps to a real vault note.
5. Take one related path or secret route.
6. End on an overhead or wide shot.

If a stranger cannot understand the idea in about 10 seconds, the world or framing is too complicated.

## Virality Angle

Virality does not need to be broad consumer virality.

Engineer-facing virality is enough if the artifact is shareable.

Distribution targets:

- X
- LinkedIn
- GrowthX community
- Obsidian communities
- builder and engineering circles

Best share lines:

- I turned my Obsidian vault into a Minecraft world.
- I built a walkable memory palace for my notes in Minecraft.

## Self-Serve Later

This is not the current priority.

The current priority is a strong functional demo on your own server.

After that works, the virality loop should become: other developers point Mine Palace at their own vault and deploy it to their own Minecraft server.

That later phase should include:

1. one-command flat-world bootstrap that creates a new safe world without touching an existing one
2. one-command deploy path for common setups like Docker, Coolify, or hosted RCON servers
3. a public sample engineer vault so people can test before using private notes
4. a short server-owner guide for memory, ports, backups, and safe coordinates
5. one share artifact per run: preview map, screenshot card, or flythrough-ready overview
6. a lightweight landing page with one clear action: generate your world, try the sample, or join the waitlist

The goal is not generic markdown import.

The goal is: a developer sees the demo and thinks, I want this on my own server tonight.

## Success Criteria

The project is in good shape for the buildathon if it hits these points:

1. the world is real and explorable in Minecraft
2. the note-to-place mapping is obvious
3. the public demo uses a safe, curated sample vault
4. the flythrough is legible without explanation
5. there is a clear action after viewing the demo

## Open Questions

These should be resolved during implementation, not abstractly debated:

1. which block interaction is most reliable on the live server for note content: lectern, barrel, or shelf-adjacent storage?
2. how much readable text should be shown in-world before it becomes cluttered?
3. what is the ideal district count for a 30-second demo?
4. should link paths be explicit walkways or rarer portal-like reveals?

## Recommendation

Stay with the original thesis.

Do not pivot back to a simple library and do not widen into a generic markdown visualization product.

Build the walkable Minecraft memory palace, demo it with a curated engineer vault, and optimize the next week of work around the single strongest flythrough you can produce.
