"""ESKD rules for a parts list (перечень элементов, GOST 2.701): grouping, ranges, wrapping, pages.

Everything here is pure: lists in, lists out. No files, no drawing.
"""

from itertools import groupby

from eskd_bom.models import BLANK, Component, Row

# Group headings by letter code (GOST 2.710). Used when a group has more than one element.
GROUP_NAMES = {
    "BQ": "Пьезоэлементы",
    "C": "Конденсаторы",
    "DA": "Микросхемы аналоговые",
    "DD": "Микросхемы цифровые",
    "FU": "Предохранители",
    "HL": "Приборы световой сигнализации",
    "K": "Реле",
    "L": "Дроссели",
    "Q": "Выключатели автоматические",
    "R": "Резисторы",
    "RK": "Терморезисторы",
    "SA": "Выключатели",
    "SB": "Кнопки",
    "VD": "Диоды",
    "VT": "Транзисторы",
    "XP": "Вилки",
    "XS": "Розетки",
    "ZQ": "Резонаторы кварцевые",
}

FIRST_SHEET_ROWS = 29  # (287 working height - 15 header - 40 title block form 2) / 8 mm
NEXT_SHEET_ROWS = 32  # (287 - 15 header - 15 title block form 2a) / 8 mm


def build_rows(components: list[Component]) -> list[Row]:
    """Sort by letter code and number, merge identical neighbours into ranges, add group headings."""
    _reject_duplicates(components)
    ordered = sorted(components, key=lambda c: (c.prefix, c.number))

    rows: list[Row] = []
    for prefix, group in groupby(ordered, key=lambda c: c.prefix):
        group = list(group)
        if rows:
            rows.append(BLANK)
        if len(group) > 1 and prefix in GROUP_NAMES:
            rows.append(Row(name=GROUP_NAMES[prefix], is_heading=True))
        rows.extend(_range_row(run) for run in _runs(group))
    return rows


def wrap_rows(rows: list[Row], name_chars: int, note_chars: int) -> list[Row]:
    """Split long names and notes onto continuation rows, as ESKD allows."""
    wrapped: list[Row] = []
    for row in rows:
        names = _wrap(row.name, name_chars)
        notes = _wrap(row.note, note_chars)
        for i in range(max(len(names), len(notes))):
            first = i == 0
            wrapped.append(
                Row(
                    designator=row.designator if first else "",
                    name=names[i] if i < len(names) else "",
                    quantity=row.quantity if first else None,
                    note=notes[i] if i < len(notes) else "",
                    is_heading=row.is_heading,
                )
            )
    return wrapped


def paginate(rows: list[Row], first: int = FIRST_SHEET_ROWS, rest: int = NEXT_SHEET_ROWS) -> list[list[Row]]:
    """Split rows into sheets. A heading never ends a sheet: it moves to the next one with its group."""
    pages: list[list[Row]] = []
    remaining = list(rows)
    capacity = first
    while remaining:
        page = remaining[:capacity]
        while len(page) > 1 and len(remaining) > len(page) and (page[-1].is_heading or page[-1] == BLANK):
            page.pop()
        pages.append(page)
        remaining = remaining[len(page):]
        if remaining and remaining[0] == BLANK:
            remaining = remaining[1:]
        capacity = rest
    return pages or [[]]


def _reject_duplicates(components: list[Component]) -> None:
    seen: set[str] = set()
    for component in components:
        if component.designator in seen:
            raise ValueError(f"designator {component.designator} appears more than once")
        seen.add(component.designator)


def _runs(group: list[Component]) -> list[list[Component]]:
    """Consecutive numbers with the same name and note form one run (R1, R2, R3 -> one row)."""
    runs: list[list[Component]] = []
    for component in group:
        last = runs[-1][-1] if runs else None
        if (
            last is not None
            and component.number == last.number + 1
            and (component.name, component.note) == (last.name, last.note)
        ):
            runs[-1].append(component)
        else:
            runs.append([component])
    return runs


def _range_row(run: list[Component]) -> Row:
    first, last = run[0], run[-1]
    if len(run) == 1:
        designator = first.designator
    elif len(run) == 2:
        designator = f"{first.designator}, {last.designator}"
    else:
        designator = f"{first.designator}...{last.designator}"
    return Row(designator=designator, name=first.name, quantity=len(run), note=first.note)


def _wrap(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
