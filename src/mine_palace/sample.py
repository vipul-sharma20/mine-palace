from __future__ import annotations

from pathlib import Path

SAMPLE_NOTES = {
    "Projects/incident-compass.md": """# Incident Compass

Build a system that turns incident notes into reusable patterns for future on-call shifts.

Linked work:
- [[Incidents/april-outage-retrospective]]
- [[Meetings/reliability-review]]
- [[LLM/postmortem-summarizer]]
""",
    "Projects/memory-palace-launch.md": """# Memory Palace Launch

Turn markdown notes into a Minecraft world people can walk through and share as a flythrough.

The hook should be specific to engineers using Obsidian.

Related:
- [[Projects/incident-compass]]
- [[LLM/devrel-angles]]
""",
    "Incidents/april-outage-retrospective.md": """# April Outage Retrospective

Root cause was hidden coupling in the deploy path. The fix was small; the visibility problem was large.

Next steps:
- tighten rollback muscle memory
- link every incident to a standing review

Links:
- [[Meetings/reliability-review]]
- [[People/staff-engineer-1-1]]
""",
    "Incidents/cache-miss-cascade.md": """# Cache Miss Cascade

The scary part was not latency, it was confidence. Once dashboards disagreed, every decision slowed down.

Follow-ups:
- [[Projects/incident-compass]]
- [[Meetings/weekly-systems]]
""",
    "Meetings/reliability-review.md": """# Reliability Review

We need fewer dashboards and more operating stories. Every graph should answer a specific operational question.

References:
- [[Incidents/april-outage-retrospective]]
- [[People/staff-engineer-1-1]]
""",
    "Meetings/weekly-systems.md": """# Weekly Systems

The team wants one place where architecture decisions, incidents, and follow-up tasks connect cleanly.

Open questions:
- [[LLM/postmortem-summarizer]]
- [[Projects/memory-palace-launch]]
""",
    "LLM/postmortem-summarizer.md": """# Postmortem Summarizer

Use a model to compress a long incident timeline into the three decisions that mattered.

We should keep humans in the loop for final wording.

References:
- [[Incidents/april-outage-retrospective]]
- [[Meetings/reliability-review]]
""",
    "LLM/devrel-angles.md": """# DevRel Angles

The project is stronger if it gives the user a strong share artifact: a world map, a flythrough, and one magical note reveal.

Related work:
- [[Projects/memory-palace-launch]]
""",
    "People/staff-engineer-1-1.md": """# Staff Engineer 1:1

Theme of the conversation: systems clarity compounds faster than heroics.

Useful follow-ups:
- [[Meetings/reliability-review]]
- [[Projects/incident-compass]]
""",
    "Career/what-i-want-to-build.md": """# What I Want To Build

I want to build tools that make invisible systems legible. The best demos compress complexity into one strong visual.

Related:
- [[Projects/memory-palace-launch]]
- [[LLM/devrel-angles]]
""",
}


def write_sample_vault(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for relative_path, content in SAMPLE_NOTES.items():
        path = destination / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
    return destination
