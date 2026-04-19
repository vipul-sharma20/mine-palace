from __future__ import annotations

import math
from collections import defaultdict

from .models import DistrictMarker, DistrictPlan, NotePlacement, VaultNote, WorldPlan

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

MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def build_world_plan(
    notes: list[VaultNote],
    *,
    name: str,
    source_vault,
    origin_x: int = 0,
    origin_y: int = 64,
    origin_z: int = 0,
    layout: str = "vault",
) -> WorldPlan:
    if layout == "diary":
        return _build_diary_world_plan(
            notes,
            name=name,
            source_vault=source_vault,
            origin_x=origin_x,
            origin_y=origin_y,
            origin_z=origin_z,
        )

    return _build_vault_world_plan(
        notes,
        name=name,
        source_vault=source_vault,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
    )


def _build_vault_world_plan(
    notes: list[VaultNote],
    *,
    name: str,
    source_vault,
    origin_x: int,
    origin_y: int,
    origin_z: int,
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
            _build_vault_district(
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


def _build_diary_world_plan(
    notes: list[VaultNote],
    *,
    name: str,
    source_vault,
    origin_x: int,
    origin_y: int,
    origin_z: int,
) -> WorldPlan:
    grouped: dict[int, list[VaultNote]] = defaultdict(list)
    for note in notes:
        if note.year is not None:
            grouped[note.year].append(note)

    years = sorted(grouped)
    if not years:
        raise ValueError("No dated notes found to build a diary world plan")

    drafts: list[DistrictPlan] = []
    for index, year in enumerate(years):
        year_notes = sorted(grouped[year], key=_diary_note_key)
        drafts.append(
            _build_diary_district(
                str(year),
                year_notes,
                center_x=0,
                center_z=0,
                origin_y=origin_y,
                palette=PALETTE_ORDER[index % len(PALETTE_ORDER)],
            )
        )

    max_span = max(max(district.width, district.depth) for district in drafts)
    if len(drafts) == 1:
        radius = 0
    else:
        radius = max(
            110,
            math.ceil((max_span + 28) / (2 * math.sin(math.pi / len(drafts)))),
        )

    districts: list[DistrictPlan] = []
    for index, draft in enumerate(drafts):
        angle = (-math.pi / 2) + (2 * math.pi * index / len(drafts))
        center_x = origin_x + round(math.cos(angle) * radius)
        center_z = origin_z + round(math.sin(angle) * radius)
        entrance_side = _entrance_side_facing_hub(center_x, center_z, origin_x, origin_z)
        districts.append(
            _translate_district(
                draft,
                center_x=center_x,
                center_z=center_z,
                entrance_side=entrance_side,
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


def _build_vault_district(
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
        entrance_side="north",
        palette=palette,
        notes=placements,
    )


def _build_diary_district(
    name: str,
    notes: list[VaultNote],
    *,
    center_x: int,
    center_z: int,
    origin_y: int,
    palette: str,
) -> DistrictPlan:
    months: dict[int, list[VaultNote]] = defaultdict(list)
    for note in notes:
        if note.month is not None:
            months[note.month].append(note)

    month_numbers = sorted(months)
    month_numbers = month_numbers or [1]
    max_notes_per_month = max(len(months.get(month, [])) for month in month_numbers)

    width = max(23, 12 + max_notes_per_month * 5)
    depth = max(23, 10 + len(month_numbers) * 5)
    entrance_x = center_x
    entrance_z = center_z - depth // 2

    start_x = center_x - width // 2 + 6
    start_z = center_z - depth // 2 + 4
    month_label_x = center_x - width // 2 + 1

    placements: list[NotePlacement] = []
    markers: list[DistrictMarker] = []
    for lane_index, month in enumerate(month_numbers):
        lane_z = start_z + lane_index * 5
        month_notes = sorted(months.get(month, []), key=_diary_note_key)
        markers.append(
            DistrictMarker(
                x=month_label_x,
                y=origin_y + 1,
                z=lane_z + 1,
                lines=[MONTH_NAMES[month - 1], f"{len(month_notes)} days", "", ""],
            )
        )
        for column, note in enumerate(month_notes):
            x = start_x + column * 5
            placements.append(NotePlacement(note=note, x=x, y=origin_y + 1, z=lane_z))

    return DistrictPlan(
        name=name,
        center_x=center_x,
        center_z=center_z,
        width=width,
        depth=depth,
        entrance_x=entrance_x,
        entrance_z=entrance_z,
        entrance_side="north",
        palette=palette,
        notes=placements,
        markers=markers,
    )


def _translate_district(
    district: DistrictPlan,
    *,
    center_x: int,
    center_z: int,
    entrance_side: str | None = None,
) -> DistrictPlan:
    delta_x = center_x - district.center_x
    delta_z = center_z - district.center_z
    resolved_side = entrance_side or district.entrance_side
    entrance_x, entrance_z = _entrance_coordinates(center_x, center_z, district.width, district.depth, resolved_side)
    return DistrictPlan(
        name=district.name,
        center_x=center_x,
        center_z=center_z,
        width=district.width,
        depth=district.depth,
        entrance_x=entrance_x,
        entrance_z=entrance_z,
        entrance_side=resolved_side,
        palette=district.palette,
        notes=[
            NotePlacement(note=placement.note, x=placement.x + delta_x, y=placement.y, z=placement.z + delta_z)
            for placement in district.notes
        ],
        markers=[
            DistrictMarker(
                x=marker.x + delta_x,
                y=marker.y,
                z=marker.z + delta_z,
                lines=marker.lines,
            )
            for marker in district.markers
        ],
    )


def _diary_note_key(note: VaultNote) -> tuple[int, int, str]:
    return (note.month or 0, note.day or 0, note.path.as_posix())


def _entrance_side_facing_hub(center_x: int, center_z: int, hub_x: int, hub_z: int) -> str:
    delta_x = hub_x - center_x
    delta_z = hub_z - center_z
    if abs(delta_x) > abs(delta_z):
        return "east" if delta_x > 0 else "west"
    return "south" if delta_z > 0 else "north"


def _entrance_coordinates(center_x: int, center_z: int, width: int, depth: int, side: str) -> tuple[int, int]:
    half_width = width // 2
    half_depth = depth // 2
    if side == "north":
        return center_x, center_z - half_depth
    if side == "south":
        return center_x, center_z + half_depth
    if side == "west":
        return center_x - half_width, center_z
    if side == "east":
        return center_x + half_width, center_z
    raise ValueError(f"Unsupported entrance side: {side}")
