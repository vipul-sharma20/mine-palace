from __future__ import annotations

import json
from pathlib import Path

from .models import DistrictPlan, NotePlacement, WorldPlan

MAX_FILL_VOLUME = 32_768

PALETTES = {
    "oak": {
        "floor": "oak_planks",
        "wall": "stripped_oak_wood",
        "trim": "smooth_stone",
        "path": "oak_planks",
        "accent": "barrel",
    },
    "spruce": {
        "floor": "spruce_planks",
        "wall": "stripped_spruce_wood",
        "trim": "stone_bricks",
        "path": "spruce_planks",
        "accent": "barrel",
    },
    "birch": {
        "floor": "birch_planks",
        "wall": "stripped_birch_wood",
        "trim": "smooth_quartz",
        "path": "birch_planks",
        "accent": "barrel",
    },
    "stone": {
        "floor": "stone_bricks",
        "wall": "chiseled_stone_bricks",
        "trim": "polished_andesite",
        "path": "stone_bricks",
        "accent": "barrel",
    },
    "dark_oak": {
        "floor": "dark_oak_planks",
        "wall": "stripped_dark_oak_wood",
        "trim": "polished_deepslate",
        "path": "dark_oak_planks",
        "accent": "barrel",
    },
    "mangrove": {
        "floor": "mangrove_planks",
        "wall": "stripped_mangrove_wood",
        "trim": "mud_bricks",
        "path": "mangrove_planks",
        "accent": "barrel",
    },
    "deepslate": {
        "floor": "polished_deepslate",
        "wall": "deepslate_bricks",
        "trim": "smooth_stone",
        "path": "polished_deepslate",
        "accent": "barrel",
    },
    "jungle": {
        "floor": "jungle_planks",
        "wall": "stripped_jungle_wood",
        "trim": "cut_sandstone",
        "path": "jungle_planks",
        "accent": "barrel",
    },
}


class WorldRenderer:
    def render(
        self,
        plan: WorldPlan,
        output_dir: Path,
        *,
        include_books: bool = True,
    ) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        commands_dir = output_dir / "commands"
        mcfunction_dir = output_dir / "mcfunction"
        preview_dir = output_dir / "preview"

        commands_dir.mkdir(exist_ok=True)
        mcfunction_dir.mkdir(exist_ok=True)
        preview_dir.mkdir(exist_ok=True)

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(plan.to_manifest(), indent=2),
            encoding="utf-8",
        )

        build_commands = self._build_commands(plan)
        build_txt = commands_dir / "build.txt"
        build_mcfunction = mcfunction_dir / "build.mcfunction"
        build_txt.write_text("\n".join(build_commands) + "\n", encoding="utf-8")
        build_mcfunction.write_text("\n".join(build_commands) + "\n", encoding="utf-8")

        clear_commands = self._clear_commands(plan)
        clear_txt = commands_dir / "clear.txt"
        clear_mcfunction = mcfunction_dir / "clear.mcfunction"
        clear_txt.write_text("\n".join(clear_commands) + "\n", encoding="utf-8")
        clear_mcfunction.write_text("\n".join(clear_commands) + "\n", encoding="utf-8")

        books_path = commands_dir / "books.txt"
        books_function = mcfunction_dir / "books.mcfunction"
        if include_books:
            book_commands = self._book_commands(plan)
            books_path.write_text("\n".join(book_commands) + "\n", encoding="utf-8")
            books_function.write_text("\n".join(book_commands) + "\n", encoding="utf-8")
        else:
            books_path.write_text("", encoding="utf-8")
            books_function.write_text("", encoding="utf-8")

        preview_path = preview_dir / "index.html"
        preview_path.write_text(self._render_preview(plan), encoding="utf-8")

        return {
            "manifest": manifest_path,
            "clear_commands": clear_txt,
            "build_commands": build_txt,
            "book_commands": books_path,
            "clear_mcfunction": clear_mcfunction,
            "build_mcfunction": build_mcfunction,
            "book_mcfunction": books_function,
            "preview": preview_path,
        }

    def _clear_commands(self, plan: WorldPlan) -> list[str]:
        bounds = plan.bounds
        ground_y = plan.origin_y
        commands = [f"# Clear Mine Palace bounds for {plan.name}"]
        commands.extend(
            _fill_commands(
                bounds["min_x"],
                bounds["min_y"],
                bounds["min_z"],
                bounds["max_x"],
                bounds["max_y"],
                bounds["max_z"],
                "air",
            )
        )
        commands.extend(
            _fill_commands(
                bounds["min_x"],
                ground_y,
                bounds["min_z"],
                bounds["max_x"],
                ground_y,
                bounds["max_z"],
                "grass_block",
            )
        )
        return commands

    def _build_commands(self, plan: WorldPlan) -> list[str]:
        commands: list[str] = [
            f"# Mine Palace build for {plan.name}",
            "time set day",
            "weather clear",
            "gamerule advance_time false",
            "gamerule advance_weather false",
            "gamerule command_block_output false",
            "gamerule send_command_feedback false",
        ]
        commands.extend(self._render_hub(plan))

        for district in plan.districts:
            commands.extend(self._connect_hub_to_district(plan, district))
            commands.extend(self._render_district(plan, district))

        return commands

    def _render_hub(self, plan: WorldPlan) -> list[str]:
        y = plan.origin_y
        r = plan.hub_radius
        outer = r + 2
        inner = r - 2
        commands = [
            f"fill {plan.origin_x - outer} {y} {plan.origin_z - outer} {plan.origin_x + outer} {y} {plan.origin_z + outer} stone_bricks",
            f"fill {plan.origin_x - inner} {y} {plan.origin_z - inner} {plan.origin_x + inner} {y} {plan.origin_z + inner} polished_andesite",
            f"fill {plan.origin_x - outer} {y + 1} {plan.origin_z - outer} {plan.origin_x + outer} {y + 5} {plan.origin_z + outer} air",
            f"fill {plan.origin_x - outer} {y + 1} {plan.origin_z - outer} {plan.origin_x + outer} {y + 1} {plan.origin_z - outer} smooth_stone",
            f"fill {plan.origin_x - outer} {y + 1} {plan.origin_z + outer} {plan.origin_x + outer} {y + 1} {plan.origin_z + outer} smooth_stone",
            f"fill {plan.origin_x - outer} {y + 1} {plan.origin_z - outer} {plan.origin_x - outer} {y + 1} {plan.origin_z + outer} smooth_stone",
            f"fill {plan.origin_x + outer} {y + 1} {plan.origin_z - outer} {plan.origin_x + outer} {y + 1} {plan.origin_z + outer} smooth_stone",
            f"fill {plan.origin_x - 1} {y} {plan.origin_z - 1} {plan.origin_x + 1} {y} {plan.origin_z + 1} chiseled_stone_bricks",
            f"setblock {plan.origin_x} {y + 1} {plan.origin_z} lodestone",
            self._standing_sign(
                plan.origin_x,
                y + 2,
                plan.origin_z - 2,
                ["Mine Palace", plan.name[:15], "Walk the", "vault"],
            ),
        ]

        commands.extend(
            self._column_commands(plan.origin_x - 5, y + 1, y + 4, plan.origin_z - 5, "chiseled_stone_bricks")
        )
        commands.extend(
            self._column_commands(plan.origin_x + 5, y + 1, y + 4, plan.origin_z - 5, "chiseled_stone_bricks")
        )
        commands.extend(
            self._column_commands(plan.origin_x - 5, y + 1, y + 4, plan.origin_z + 5, "chiseled_stone_bricks")
        )
        commands.extend(
            self._column_commands(plan.origin_x + 5, y + 1, y + 4, plan.origin_z + 5, "chiseled_stone_bricks")
        )
        commands.extend(
            [
                f"fill {plan.origin_x - 5} {y + 4} {plan.origin_z - 5} {plan.origin_x + 5} {y + 4} {plan.origin_z - 5} smooth_stone",
                f"fill {plan.origin_x - 5} {y + 4} {plan.origin_z + 5} {plan.origin_x + 5} {y + 4} {plan.origin_z + 5} smooth_stone",
                f"fill {plan.origin_x - 5} {y + 4} {plan.origin_z - 5} {plan.origin_x - 5} {y + 4} {plan.origin_z + 5} smooth_stone",
                f"fill {plan.origin_x + 5} {y + 4} {plan.origin_z - 5} {plan.origin_x + 5} {y + 4} {plan.origin_z + 5} smooth_stone",
                f"setblock {plan.origin_x - 5} {y + 5} {plan.origin_z - 5} lantern",
                f"setblock {plan.origin_x + 5} {y + 5} {plan.origin_z - 5} lantern",
                f"setblock {plan.origin_x - 5} {y + 5} {plan.origin_z + 5} lantern",
                f"setblock {plan.origin_x + 5} {y + 5} {plan.origin_z + 5} lantern",
            ]
        )

        for index, district in enumerate(plan.districts[:8]):
            sign_x = plan.origin_x - 7 + (index % 4) * 5
            sign_z = plan.origin_z + 5 if index < 4 else plan.origin_z + 7
            commands.extend(
                [
                    f"setblock {sign_x} {y + 1} {sign_z} smooth_stone",
                    self._standing_sign(
                        sign_x,
                        y + 2,
                        sign_z,
                        [district.name[:15], f"{len(district.notes)} notes", "District", ""],
                    ),
                ]
            )

        return commands

    def _connect_hub_to_district(self, plan: WorldPlan, district: DistrictPlan) -> list[str]:
        y = plan.origin_y
        palette = PALETTES[district.palette]
        path_block = palette["path"]
        x1 = plan.origin_x
        z1 = plan.origin_z + plan.hub_radius + 1
        x2 = district.entrance_x
        z2 = district.entrance_z - 1

        commands = [
            f"fill {min(x1, x2)} {y} {z1 - 1} {max(x1, x2)} {y} {z1 + 1} {path_block}",
            f"fill {min(x1, x2)} {y} {z1 - 2} {max(x1, x2)} {y} {z1 - 2} {palette['trim']}",
            f"fill {min(x1, x2)} {y} {z1 + 2} {max(x1, x2)} {y} {z1 + 2} {palette['trim']}",
            f"fill {x2 - 1} {y} {min(z1, z2)} {x2 + 1} {y} {max(z1, z2)} {path_block}",
            f"fill {x2 - 2} {y} {min(z1, z2)} {x2 - 2} {y} {max(z1, z2)} {palette['trim']}",
            f"fill {x2 + 2} {y} {min(z1, z2)} {x2 + 2} {y} {max(z1, z2)} {palette['trim']}",
        ]
        return commands

    def _render_district(self, plan: WorldPlan, district: DistrictPlan) -> list[str]:
        palette = PALETTES[district.palette]
        y = plan.origin_y
        half_width = district.width // 2
        half_depth = district.depth // 2
        x1 = district.center_x - half_width
        x2 = district.center_x + half_width
        z1 = district.center_z - half_depth
        z2 = district.center_z + half_depth

        commands = [
            f"fill {x1} {y} {z1} {x2} {y} {z2} {palette['floor']}",
            f"fill {x1} {y - 1} {z1} {x2} {y - 1} {z2} {palette['trim']}",
            f"fill {x1} {y + 1} {z1} {x2} {y + 5} {z2} air",
            f"fill {x1} {y} {z1} {x2} {y} {z1} {palette['trim']}",
            f"fill {x1} {y} {z2} {x2} {y} {z2} {palette['trim']}",
            f"fill {x1} {y} {z1} {x1} {y} {z2} {palette['trim']}",
            f"fill {x2} {y} {z1} {x2} {y} {z2} {palette['trim']}",
            f"fill {district.entrance_x - 1} {y} {z1} {district.entrance_x + 1} {y} {z2 - 2} {palette['path']}",
            f"fill {x1} {y + 4} {z1} {district.entrance_x - 2} {y + 4} {z1} {palette['trim']}",
            f"fill {district.entrance_x + 2} {y + 4} {z1} {x2} {y + 4} {z1} {palette['trim']}",
            f"fill {x1} {y + 4} {z2} {x2} {y + 4} {z2} {palette['trim']}",
            f"fill {x1} {y + 4} {z1} {x1} {y + 4} {z2} {palette['trim']}",
            f"fill {x2} {y + 4} {z1} {x2} {y + 4} {z2} {palette['trim']}",
            self._standing_sign(
                district.entrance_x,
                y + 1,
                z1 - 1,
                [district.name[:15], f"{len(district.notes)} notes", "Enter", ""],
            ),
        ]

        commands.extend(self._column_commands(x1, y + 1, y + 4, z1, palette["wall"]))
        commands.extend(self._column_commands(x2, y + 1, y + 4, z1, palette["wall"]))
        commands.extend(self._column_commands(x1, y + 1, y + 4, z2, palette["wall"]))
        commands.extend(self._column_commands(x2, y + 1, y + 4, z2, palette["wall"]))
        commands.extend(self._column_commands(district.entrance_x - 2, y + 1, y + 4, z1, palette["wall"]))
        commands.extend(self._column_commands(district.entrance_x + 2, y + 1, y + 4, z1, palette["wall"]))
        commands.extend(
            [
                f"setblock {district.entrance_x - 2} {y + 5} {z1} lantern",
                f"setblock {district.entrance_x + 2} {y + 5} {z1} lantern",
            ]
        )

        for note in district.notes:
            commands.extend(self._render_note_alcove(note, palette))

        for marker in district.markers:
            commands.append(self._standing_sign(marker.x, marker.y, marker.z, marker.lines))

        return commands

    def _render_note_alcove(self, placement: NotePlacement, palette: dict[str, str]) -> list[str]:
        x = placement.x
        y = placement.y
        z = placement.z
        title = _linebreak_title(placement.note.title)
        excerpt = placement.note.excerpt[:15]
        meta = placement.note.path.as_posix()[:15]

        commands = [
            f"fill {x - 2} {y - 1} {z - 2} {x + 2} {y - 1} {z + 2} {palette['trim']}",
            f"fill {x - 2} {y} {z - 2} {x + 2} {y + 3} {z - 2} {palette['wall']}",
            f"fill {x - 2} {y} {z - 2} {x - 2} {y + 2} {z + 1} {palette['wall']}",
            f"fill {x + 2} {y} {z - 2} {x + 2} {y + 2} {z + 1} {palette['wall']}",
            f"fill {x - 2} {y + 3} {z - 2} {x + 2} {y + 3} {z - 2} {palette['trim']}",
            f"setblock {x} {y} {z - 1} chiseled_bookshelf",
            f"setblock {x - 1} {y} {z - 1} bookshelf",
            f"setblock {x + 1} {y} {z - 1} bookshelf",
            f"setblock {x} {y} {z} lectern[facing=south,has_book=false]",
            f"setblock {x - 2} {y} {z + 1} lantern",
            f"setblock {x + 2} {y} {z + 1} lantern",
            self._standing_sign(
                x - 1,
                y,
                z + 1,
                [title[0], title[1], excerpt, ""],
            ),
            self._standing_sign(
                x + 1,
                y,
                z + 1,
                [meta, f"{len(placement.note.links)} links", f"{len(placement.note.tags)} tags", ""],
            ),
        ]

        return commands

    def _column_commands(self, x: int, y1: int, y2: int, z: int, block: str) -> list[str]:
        return [f"fill {x} {y1} {z} {x} {y2} {z} {block}"]

    def _book_commands(self, plan: WorldPlan) -> list[str]:
        commands = [f"# Experimental written-book placement for {plan.name}"]
        for district in plan.districts:
            for placement in district.notes:
                commands.extend(self._shelf_book_commands(placement))
                commands.append(self._lectern_book_command(placement))
        return commands

    def _shelf_book_commands(self, placement: NotePlacement) -> list[str]:
        x = placement.x
        y = placement.y
        z = placement.z - 1
        note_book = _written_book_item(placement.note.title, _book_pages(placement.note.content))
        return [
            f"setblock {x} {y} {z} air",
            f"setblock {x} {y} {z} chiseled_bookshelf",
            f"item replace block {x} {y} {z} container.0 with {note_book} 1",
        ]

    def _lectern_book_command(self, placement: NotePlacement) -> str:
        note = placement.note
        pages = ",".join(_lectern_page_component(page) for page in _book_pages(note.content))
        return (
            f"data merge block {placement.x} {placement.y} {placement.z} "
            "{Book:{id:'minecraft:written_book',count:1,components:{'minecraft:written_book_content':{"
            f"pages:[{pages}],author:{_snbt_single_quote('Mine Palace')},title:{_lectern_title_component(note.title)}"
            "}}},Page:0}"
        )

    def _standing_sign(self, x: int, y: int, z: int, lines: list[str]) -> str:
        block = "oak_sign[rotation=8]"
        payload = _sign_nbt(lines)
        return f"setblock {x} {y} {z} {block}{payload}"

    def _render_preview(self, plan: WorldPlan) -> str:
        manifest = json.dumps(plan.to_manifest())
        template = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Mine Palace Preview</title>
    <style>
      :root {{
        --bg: #efe4d0;
        --surface: #fbf7ef;
        --ink: #1d1b18;
        --accent: #3f6b4f;
        --accent-2: #9d5c3d;
        --line: #d8c7ad;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Georgia, "Iowan Old Style", serif;
        background:
          radial-gradient(circle at top, rgba(63,107,79,0.12), transparent 30%),
          linear-gradient(180deg, #f8f1e4, var(--bg));
        color: var(--ink);
      }}
      .page {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 32px 20px 64px;
      }}
      h1 {{
        margin: 0;
        font-size: clamp(2.4rem, 5vw, 4rem);
        line-height: 0.95;
        letter-spacing: -0.04em;
      }}
      p.lede {{
        max-width: 760px;
        font-size: 1.1rem;
        color: rgba(29, 27, 24, 0.82);
      }}
      .stats {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
        margin: 24px 0 32px;
      }}
      .stat {{
        background: rgba(251, 247, 239, 0.9);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 10px 30px rgba(61, 49, 28, 0.06);
      }}
      .stat strong {{
        display: block;
        font-size: 1.8rem;
      }}
      .map-card, .districts {{
        background: rgba(251, 247, 239, 0.94);
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 20px;
        box-shadow: 0 16px 40px rgba(61, 49, 28, 0.08);
      }}
      .map-card {{
        overflow: auto;
      }}
      svg {{
        width: 100%;
        min-width: 860px;
        height: 560px;
        display: block;
      }}
      .district-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 14px;
        margin-top: 18px;
      }}
      .district {{
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 16px;
        background: linear-gradient(180deg, rgba(255,255,255,0.7), rgba(244,238,226,0.9));
      }}
      .district h2 {{
        margin: 0 0 8px;
        font-size: 1.2rem;
      }}
      ul {{
        margin: 10px 0 0;
        padding-left: 18px;
      }}
      li {{
        margin: 0 0 8px;
      }}
      .pill {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(63, 107, 79, 0.12);
        color: var(--accent);
        font-size: 0.82rem;
        margin-right: 8px;
      }}
    </style>
  </head>
  <body>
    <div class="page">
      <h1>Mine Palace</h1>
      <p class="lede">A walkable Minecraft memory palace planned from a markdown vault. This preview is the debug surface: district layout, note count, and coordinate map before you push commands to the server.</p>
      <div id="app"></div>
    </div>
    <script>
      const manifest = __MANIFEST__;

      const colors = {{
        oak: "#c2855c",
        spruce: "#8a6846",
        birch: "#d8c182",
        stone: "#8c8f97",
        dark_oak: "#5a4031",
        mangrove: "#a85e5b",
        deepslate: "#5a6166",
        jungle: "#9e7648"
      }};

      function extent(items, key) {{
        return items.reduce((acc, item) => {{
          acc.min = Math.min(acc.min, item[key]);
          acc.max = Math.max(acc.max, item[key]);
          return acc;
        }}, {{ min: Infinity, max: -Infinity }});
      }}

      function renderMap(world) {{
        const districts = world.districts;
        const xBounds = extent(districts, "center_x");
        const zBounds = extent(districts, "center_z");
        const padding = 80;
        const width = 1000;
        const height = 560;
        const spanX = Math.max(1, xBounds.max - xBounds.min);
        const spanZ = Math.max(1, zBounds.max - zBounds.min);

        const scaleX = (width - padding * 2) / spanX;
        const scaleZ = (height - padding * 2) / spanZ;
        const scale = Math.min(scaleX, scaleZ);

        const toSvgX = (x) => padding + (x - xBounds.min) * scale;
        const toSvgZ = (z) => padding + (z - zBounds.min) * scale;

        const hubX = toSvgX(world.origin_x);
        const hubZ = toSvgZ(world.origin_z);

        const districtRects = districts.map((district) => {{
          const w = district.width * scale;
          const d = district.depth * scale;
          const x = toSvgX(district.center_x) - w / 2;
          const z = toSvgZ(district.center_z) - d / 2;
          const notes = district.notes.map((note) => {{
            return `<circle cx="${{toSvgX(note.x)}}" cy="${{toSvgZ(note.z)}}" r="3.5" fill="#1d1b18" opacity="0.75" />`;
          }}).join("");
          return `
            <g>
              <rect x="${{x}}" y="${{z}}" width="${{w}}" height="${{d}}" rx="14" fill="${{colors[district.palette] || "#9e7648"}}" opacity="0.22" stroke="${{colors[district.palette] || "#9e7648"}}" stroke-width="2" />
              <text x="${{x + 12}}" y="${{z + 22}}" font-size="14" font-family="Georgia" fill="#1d1b18">${{district.name}}</text>
              ${{notes}}
            </g>
          `;
        }}).join("");

        return `
          <div class="map-card">
            <span class="pill">Overhead layout</span>
            <svg viewBox="0 0 1000 560" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stop-color="#fffaf3" />
                  <stop offset="100%" stop-color="#efe4d0" />
                </linearGradient>
              </defs>
              <rect width="1000" height="560" fill="url(#bg)" rx="24" />
              <circle cx="${{hubX}}" cy="${{hubZ}}" r="26" fill="#3f6b4f" opacity="0.2" stroke="#3f6b4f" stroke-width="3" />
              <text x="${{hubX - 32}}" y="${{hubZ + 6}}" font-size="14" font-family="Georgia" fill="#1d1b18">Hub</text>
              ${{districtRects}}
            </svg>
          </div>
        `;
      }}

      function renderDistricts(world) {{
        const cards = world.districts.map((district) => {{
          const topNotes = district.notes.slice(0, 4).map((note) => {{
            const title = note.note.title;
            const excerpt = note.note.excerpt;
            return `<li><strong>${{title}}</strong><br /><span>${{excerpt}}</span></li>`;
          }}).join("");
          return `
            <article class="district">
              <span class="pill">${{district.palette}}</span>
              <h2>${{district.name}}</h2>
              <div>${{district.notes.length}} notes</div>
              <div>Center: ${{district.center_x}}, ${{district.center_z}}</div>
              <ul>${{topNotes}}</ul>
            </article>
          `;
        }}).join("");

        return `<div class="districts"><span class="pill">Districts</span><div class="district-grid">${{cards}}</div></div>`;
      }}

      const app = document.getElementById("app");
      app.innerHTML = `
        <div class="stats">
          <div class="stat"><strong>${{manifest.districts.length}}</strong>districts</div>
          <div class="stat"><strong>${{manifest.note_count}}</strong>notes</div>
          <div class="stat"><strong>${{manifest.source_vault.split("/").slice(-1)[0]}}</strong>source</div>
        </div>
        ${renderMap(manifest)}
        <div style="height:16px"></div>
        ${renderDistricts(manifest)}
      `;
    </script>
  </body>
</html>
"""
        return template.replace("__MANIFEST__", manifest)


def _sign_nbt(lines: list[str]) -> str:
    padded = (lines + ["", "", "", ""])[:4]
    messages = ",".join(_snbt_single_quote(line[:15]) for line in padded)
    return "{front_text:{messages:[" + messages + "]},is_waxed:1b}"


def _snbt_single_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return "'" + escaped + "'"


def _book_pages(text: str) -> list[str]:
    compact = " ".join(text.split())
    if not compact:
        return ["Empty note"]
    chunk_size = 160
    max_chars = 480
    return [compact[index : index + chunk_size] for index in range(0, min(len(compact), max_chars), chunk_size)]


def _linebreak_title(title: str) -> tuple[str, str]:
    words = title.split()
    if len(words) <= 2:
        return (title[:15], "")
    midpoint = max(1, len(words) // 2)
    line_1 = " ".join(words[:midpoint])[:15]
    line_2 = " ".join(words[midpoint:])[:15]
    return (line_1, line_2)


def _lectern_page_component(text: str) -> str:
    return "{raw:" + _snbt_single_quote(text) + "}"


def _lectern_title_component(title: str) -> str:
    return "{raw:" + _snbt_single_quote(title[:32]) + "}"


def _written_book_item(title: str, pages: list[str]) -> str:
    page_components = ",".join(_lectern_page_component(page) for page in pages)
    return (
        "written_book[written_book_content={"
        f"title:{_lectern_title_component(title)},author:{_snbt_single_quote('Mine Palace')},pages:[{page_components}]"
        "}]"
    )


def _fill_commands(
    x1: int,
    y1: int,
    z1: int,
    x2: int,
    y2: int,
    z2: int,
    block: str,
) -> list[str]:
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    z1, z2 = sorted((z1, z2))

    width = x2 - x1 + 1
    height = y2 - y1 + 1
    depth = z2 - z1 + 1
    volume = width * height * depth
    if volume <= MAX_FILL_VOLUME:
        return [f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}"]

    max_x_span = max(1, MAX_FILL_VOLUME // (height * depth))
    if max_x_span < width:
        commands = []
        start_x = x1
        while start_x <= x2:
            end_x = min(start_x + max_x_span - 1, x2)
            commands.extend(_fill_commands(start_x, y1, z1, end_x, y2, z2, block))
            start_x = end_x + 1
        return commands

    max_z_span = max(1, MAX_FILL_VOLUME // height)
    commands = []
    start_z = z1
    while start_z <= z2:
        end_z = min(start_z + max_z_span - 1, z2)
        commands.extend(_fill_commands(x1, y1, start_z, x2, y2, end_z, block))
        start_z = end_z + 1
    return commands
