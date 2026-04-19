from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class VaultNote:
    slug: str
    title: str
    path: Path
    district: str
    content: str
    excerpt: str
    links: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    year: int | None = None
    month: int | None = None
    day: int | None = None

    def to_manifest(self) -> dict[str, object]:
        payload = asdict(self)
        payload["path"] = self.path.as_posix()
        return payload


@dataclass(slots=True)
class NotePlacement:
    note: VaultNote
    x: int
    y: int
    z: int

    def to_manifest(self) -> dict[str, object]:
        return {
            "note": self.note.to_manifest(),
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }


@dataclass(slots=True)
class DistrictMarker:
    x: int
    y: int
    z: int
    lines: list[str]

    def to_manifest(self) -> dict[str, object]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "lines": self.lines,
        }


@dataclass(slots=True)
class DistrictPlan:
    name: str
    center_x: int
    center_z: int
    width: int
    depth: int
    entrance_x: int
    entrance_z: int
    palette: str
    notes: list[NotePlacement] = field(default_factory=list)
    markers: list[DistrictMarker] = field(default_factory=list)

    def to_manifest(self) -> dict[str, object]:
        return {
            "name": self.name,
            "center_x": self.center_x,
            "center_z": self.center_z,
            "width": self.width,
            "depth": self.depth,
            "entrance_x": self.entrance_x,
            "entrance_z": self.entrance_z,
            "palette": self.palette,
            "notes": [note.to_manifest() for note in self.notes],
            "markers": [marker.to_manifest() for marker in self.markers],
        }


@dataclass(slots=True)
class WorldPlan:
    name: str
    source_vault: Path
    origin_x: int
    origin_y: int
    origin_z: int
    hub_radius: int
    districts: list[DistrictPlan]

    @property
    def note_count(self) -> int:
        return sum(len(district.notes) for district in self.districts)

    @property
    def bounds(self) -> dict[str, int]:
        min_x = self.origin_x - self.hub_radius
        max_x = self.origin_x + self.hub_radius
        min_z = self.origin_z - self.hub_radius
        max_z = self.origin_z + self.hub_radius

        for district in self.districts:
            min_x = min(min_x, district.center_x - district.width // 2)
            max_x = max(max_x, district.center_x + district.width // 2)
            min_z = min(min_z, district.center_z - district.depth // 2)
            max_z = max(max_z, district.center_z + district.depth // 2)

        return {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": self.origin_y - 1,
            "max_y": self.origin_y + 5,
            "min_z": min_z,
            "max_z": max_z,
        }

    def to_manifest(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source_vault": self.source_vault.as_posix(),
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "origin_z": self.origin_z,
            "hub_radius": self.hub_radius,
            "note_count": self.note_count,
            "bounds": self.bounds,
            "districts": [district.to_manifest() for district in self.districts],
        }
