"""Reading components from a schematic drawn in AutoCAD.

Each element is a block reference (INSERT) with attributes. The attribute tags are configurable
because every drawing template names them differently.
"""

from dataclasses import dataclass, field
from pathlib import Path

import ezdxf

from eskd_bom.models import Component


@dataclass(frozen=True)
class AttributeTags:
    designator: tuple[str, ...] = ("REF", "DESIGNATOR", "POS", "ПОЗ")
    name: tuple[str, ...] = ("NAME", "VALUE", "НАИМ")
    note: tuple[str, ...] = ("NOTE", "ПРИМ")


@dataclass
class ReadResult:
    components: list[Component]
    skipped_blocks: list[str] = field(default_factory=list)


def read_components(path: Path, tags: AttributeTags = AttributeTags()) -> ReadResult:
    """Collect components from every block reference in model space that has a designator attribute."""
    doc = ezdxf.readfile(path)
    components: list[Component] = []
    skipped: list[str] = []

    for insert in doc.modelspace().query("INSERT"):
        values = {attrib.dxf.tag.upper(): attrib.dxf.text.strip() for attrib in insert.attribs}
        designator = _first(values, tags.designator)
        if not designator:
            skipped.append(insert.dxf.name)
            continue
        name = _first(values, tags.name)
        if not name:
            raise ValueError(f"block {insert.dxf.name} ({designator}) has no name attribute {tags.name}")
        components.append(Component(designator, name, _first(values, tags.note)))

    return ReadResult(components, skipped)


def _first(values: dict[str, str], candidates: tuple[str, ...]) -> str:
    for tag in candidates:
        if values.get(tag.upper()):
            return values[tag.upper()]
    return ""
