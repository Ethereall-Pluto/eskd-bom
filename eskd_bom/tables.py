"""Component lists as CSV and Excel, so a parts list can be checked or edited outside AutoCAD."""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from eskd_bom.models import Component

HEADER = ["Designator", "Name", "Note"]


def write_csv(components: list[Component], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for c in components:
            writer.writerow([c.designator, c.name, c.note])


def read_csv(path: Path) -> list[Component]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = {"Designator", "Name"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}; expected {HEADER}")
        return [Component(r["Designator"].strip(), r["Name"].strip(), (r.get("Note") or "").strip()) for r in reader]


def write_xlsx(components: list[Component], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Components"
    ws.append(HEADER)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for c in components:
        ws.append([c.designator, c.name, c.note])
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 30
    ws.freeze_panes = "A2"
    wb.save(path)


def write_table(components: list[Component], path: Path) -> None:
    writers = {".csv": write_csv, ".xlsx": write_xlsx}
    if path.suffix.lower() not in writers:
        raise ValueError(f"output must be .csv or .xlsx, got {path.name}")
    writers[path.suffix.lower()](components, path)
