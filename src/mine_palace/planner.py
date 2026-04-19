from __future__ import annotations

import math
from collections import defaultdict

from .models import DistrictPlan, NotePlacement, VaultNote, WorldPlan

PALETTE_ORDER = [
    "oak",
    "spruce",
    "birch",
    "stone",
    "dark_oak",
    "mangrove",
    "deepslate",
    "jungle",
]


def build_world_plan(
    notes: list[VaultNote],
    *,
    name: str,
    source_vault,
    origin_x: int = 0,
    origin_y: int = 64,
    origin_z: int = 0,
) -> WorldPlan:
    grouped: dict[str, list[VaultNote]] = defaultdict(list)
    for note in notes:
        grouped[note.district].append(note)

    district_names = sorted(grouped, key=lambda district: (-len(grouped[district]), district.lower()))
    if not district_names:
        raise ValueError("No notes found to build a world plan")

    spacing = 44
    columns = math.ceil(math.sqrt(len(district_names)))
    rows = math.ceil(len(district_names) / columns)
    x_offset = (columns - 1) * spacing // 2
    z_offset = (rows - 1) * spacing // 2

    districts: list[DistrictPlan] = []
    for index, district_name in enumerate(district_names):
        row = index // columns
        column = index % columns
        center_x = origin_x + (column * spacing) - x_offset
        center_z = origin_z + (row * spacing) - z_offset
        district_notes = sorted(grouped[district_name], key=lambda note: note.path.as_posix())
        districts.append(
            _build_district(
                district_name,
                district_notes,
                center_x=center_x,
                center_z=center_z,
                origin_y=origin_y,
                palette=PALETTE_ORDER[index % len(PALETTE_ORDER)],
            )
        )

    return WorldPlan(
        name=name,
        source_vault=source_vault,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        hub_radius=8,
        districts=districts,
    )


def _build_district(
    name: str,
    notes: list[VaultNote],
    *,
    center_x: int,
    center_z: int,
    origin_y: int,
    palette: str,
) -> DistrictPlan:
    note_columns = max(2, math.ceil(math.sqrt(max(1, len(notes)))))
    note_rows = max(1, math.ceil(len(notes) / note_columns))

    width = max(19, 8 + note_columns * 5)
    depth = max(19, 10 + note_rows * 5)
    entrance_x = center_x
    entrance_z = center_z - depth // 2

    start_x = center_x - width // 2 + 4
    start_z = center_z - depth // 2 + 4

    placements: list[NotePlacement] = []
    for index, note in enumerate(notes):
        row = index // note_columns
        column = index % note_columns
        x = start_x + column * 5
        z = start_z + row * 5
        placements.append(NotePlacement(note=note, x=x, y=origin_y + 1, z=z))

    return DistrictPlan(
        name=name,
        center_x=center_x,
        center_z=center_z,
        width=width,
        depth=depth,
        entrance_x=entrance_x,
        entrance_z=entrance_z,
        palette=palette,
        notes=placements,
    )
