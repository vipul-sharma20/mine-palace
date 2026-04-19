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

VAULT_DISTRICT_GAP = 8
DIARY_NOTE_STEP = 4
DIARY_HUB_CLEARANCE = 14
DIARY_ROW_GAP = 8

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

    drafts: list[DistrictPlan] = []
    for index, district_name in enumerate(district_names):
        district_notes = sorted(grouped[district_name], key=lambda note: note.path.as_posix())
        drafts.append(
            _build_vault_district(
                district_name,
                district_notes,
                center_x=0,
                center_z=0,
                origin_y=origin_y,
                palette=PALETTE_ORDER[index % len(PALETTE_ORDER)],
            )
        )

    spacing_x = max(district.width for district in drafts) + VAULT_DISTRICT_GAP
    spacing_z = max(district.depth for district in drafts) + VAULT_DISTRICT_GAP
    columns = math.ceil(math.sqrt(len(district_names)))
    rows = math.ceil(len(district_names) / columns)
    x_offset = (columns - 1) * spacing_x // 2
    z_offset = (rows - 1) * spacing_z // 2

    districts: list[DistrictPlan] = []
    for index, draft in enumerate(drafts):
        row = index // columns
        column = index % columns
        center_x = origin_x + (column * spacing_x) - x_offset
        center_z = origin_z + (row * spacing_z) - z_offset
        districts.append(
            _translate_district(
                draft,
                center_x=center_x,
                center_z=center_z,
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

    rows = [drafts[index : index + 2] for index in range(0, len(drafts), 2)]
    row_depths = [max(district.depth for district in row) for row in rows]
    split_index = len(rows) // 2

    row_centers: list[int] = [origin_z] * len(rows)
    cursor = origin_z - DIARY_HUB_CLEARANCE
    for row_index in range(split_index - 1, -1, -1):
        depth = row_depths[row_index]
        cursor -= depth // 2
        row_centers[row_index] = cursor
        cursor -= math.ceil(depth / 2) + DIARY_ROW_GAP

    cursor = origin_z + DIARY_HUB_CLEARANCE
    for row_index in range(split_index, len(rows)):
        depth = row_depths[row_index]
        cursor += depth // 2
        row_centers[row_index] = cursor
        cursor += math.ceil(depth / 2) + DIARY_ROW_GAP

    districts: list[DistrictPlan] = []
    for row_index, row in enumerate(rows):
        center_z = row_centers[row_index]
        if len(row) == 1:
            entrance_side = "south" if center_z < origin_z else "north"
            districts.append(
                _translate_district(
                    row[0],
                    center_x=origin_x,
                    center_z=center_z,
                    entrance_side=entrance_side,
                )
            )
            continue

        left, right = row
        districts.append(
            _translate_district(
                left,
                center_x=origin_x - (DIARY_HUB_CLEARANCE + left.width // 2),
                center_z=center_z,
                entrance_side="east",
            )
        )
        districts.append(
            _translate_district(
                right,
                center_x=origin_x + (DIARY_HUB_CLEARANCE + right.width // 2),
                center_z=center_z,
                entrance_side="west",
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

    width = max(21, 11 + max_notes_per_month * DIARY_NOTE_STEP)
    depth = max(21, 9 + len(month_numbers) * DIARY_NOTE_STEP)
    entrance_x = center_x
    entrance_z = center_z - depth // 2

    start_x = center_x - width // 2 + 6
    start_z = center_z - depth // 2 + 4
    month_label_x = center_x - width // 2 + 1

    placements: list[NotePlacement] = []
    markers: list[DistrictMarker] = []
    for lane_index, month in enumerate(month_numbers):
        lane_z = start_z + lane_index * DIARY_NOTE_STEP
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
            x = start_x + column * DIARY_NOTE_STEP
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
