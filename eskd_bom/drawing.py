"""Drawing parts-list sheets into DXF.

Sheet geometry, millimetres, origin at the bottom-left corner of an A4 sheet (210 x 297):
- frame 20 mm from the left edge and 5 mm from the others (GOST 2.301), working field 185 x 287;
- table header 15 mm, rows 8 mm, columns 20 / 110 / 10 / 45 (GOST 2.701);
- title block form 2 (185 x 40) on the first sheet, form 2a (185 x 15) on the rest (GOST 2.104);
- additional graphs 19-23 on the binding margin.
Sheets are placed side by side in model space.
"""

from functools import lru_cache
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf.fonts import fonts

from eskd_bom.models import Row, TitleBlock

SHEET_W, SHEET_H = 210.0, 297.0
LEFT, MARGIN = 20.0, 5.0
SHEET_GAP = 20.0

TOP = SHEET_H - MARGIN
HEADER_H = 15.0
ROW_H = 8.0
COLUMNS = [20.0, 110.0, 10.0, 45.0]  # designator, name, quantity, note
FORM2_H, FORM2A_H = 40.0, 15.0
CHANGE_WIDTHS = [7.0, 10.0, 23.0, 15.0, 10.0]
CHANGE_LABELS = ["Изм.", "Лист", "№ докум.", "Подп.", "Дата"]

FONT_FILE = "isocpeur.ttf"  # AutoCAD's GOST-style font with Cyrillic
TEXT_H = 3.5
SMALL_H = 2.5
CHAR_W = 0.62  # average character width as a share of text height, used only to wrap long names

THICK = 50  # lineweight 0.50 mm: frame and form outlines
THIN = 18  # 0.18 mm: row lines

NAME_CHARS = int((COLUMNS[1] - 4) / (TEXT_H * CHAR_W))
NOTE_CHARS = int((COLUMNS[3] - 4) / (TEXT_H * CHAR_W))


@lru_cache(maxsize=None)
def _font(height: float):
    return fonts.make_font(FONT_FILE, height)


def _measure(value: str, height: float) -> float:
    """Real text width in mm. Without ISOCPEUR installed ezdxf measures with a wider fallback font,
    so the result errs on the side of compressing a little too much, never too little."""
    return _font(height).text_width(value)


def render(pages: list[list[Row]], title: TitleBlock, path: Path) -> None:
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.MM
    doc.styles.add("ESKD", font=FONT_FILE)
    msp = doc.modelspace()

    for index, rows in enumerate(pages):
        sheet = _Sheet(msp, x0=index * (SHEET_W + SHEET_GAP))
        first = index == 0
        block_h = FORM2_H if first else FORM2A_H
        sheet.frame()
        sheet.binding_graphs()
        sheet.table(rows, bottom=MARGIN + block_h)
        if first:
            sheet.form2(title, sheets=len(pages))
        else:
            sheet.form2a(title, sheet_no=index + 1)

    doc.saveas(path)


class _Sheet:
    """Draws one sheet. Coordinates passed to its methods are relative to the sheet's corner."""

    def __init__(self, msp, x0: float) -> None:
        self.msp = msp
        self.x0 = x0

    # primitives -------------------------------------------------------------------------------

    def line(self, x1, y1, x2, y2, weight=THIN):
        self.msp.add_line((self.x0 + x1, y1), (self.x0 + x2, y2), dxfattribs={"lineweight": weight})

    def rect(self, x, y, w, h, weight=THICK):
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self.msp.add_lwpolyline(
            [(self.x0 + px, py) for px, py in pts], close=True, dxfattribs={"lineweight": weight}
        )

    def text(self, value, x, y, height=TEXT_H, align=TextEntityAlignment.MIDDLE_LEFT, rotation=0.0, fit=None):
        """Place text; if `fit` (mm) is given and the text is wider, compress it horizontally, as drafters do."""
        if not value:
            return
        attribs = {"style": "ESKD"}
        if fit is not None:
            width = _measure(value, height)
            if width > fit:
                attribs["width"] = round(fit / width, 3)
        entity = self.msp.add_text(value, height=height, rotation=rotation, dxfattribs=attribs)
        entity.set_placement((self.x0 + x, y), align=align)

    def centered(self, value, x, y, w, h, height=TEXT_H, rotation=0.0):
        along = h if rotation else w
        self.text(value, x + w / 2, y + h / 2, height, TextEntityAlignment.MIDDLE_CENTER, rotation, fit=along - 1.0)

    # parts --------------------------------------------------------------------------------------

    def frame(self):
        self.rect(LEFT, MARGIN, SHEET_W - LEFT - MARGIN, SHEET_H - 2 * MARGIN)

    def binding_graphs(self):
        """Graphs 19-23 along the binding margin, bottom to top: 25, 35, 25, 25, 35 mm."""
        labels = ["Инв. № подл.", "Подп. и дата", "Взам. инв. №", "Инв. № дубл.", "Подп. и дата"]
        heights = [25.0, 35.0, 25.0, 25.0, 35.0]
        x_label, x_value = LEFT - 12.0, LEFT - 7.0
        y = MARGIN
        for label, h in zip(labels, heights):
            self.rect(x_label, y, 12.0, h)
            self.line(x_value, y, x_value, y + h, THICK)
            self.centered(label, x_label, y, 5.0, h, SMALL_H, rotation=90)
            y += h

    def table(self, rows: list[Row], bottom: float):
        xs = [LEFT]
        for width in COLUMNS:
            xs.append(xs[-1] + width)
        header_bottom = TOP - HEADER_H

        self.line(LEFT, header_bottom, xs[-1], header_bottom, THICK)
        for x in xs[1:-1]:
            self.line(x, bottom, x, TOP, THICK)
        self.centered("Поз.", xs[0], header_bottom + 7.5, COLUMNS[0], 7.5, SMALL_H)
        self.centered("обозначение", xs[0], header_bottom, COLUMNS[0], 7.5, SMALL_H)
        self.centered("Наименование", xs[1], header_bottom, COLUMNS[1], HEADER_H)
        self.centered("Кол.", xs[2], header_bottom, COLUMNS[2], HEADER_H, SMALL_H)
        self.centered("Примечание", xs[3], header_bottom, COLUMNS[3], HEADER_H)

        y = header_bottom
        while y - ROW_H >= bottom - 1e-6:
            y -= ROW_H
            self.line(LEFT, y, xs[-1], y)

        for i, row in enumerate(rows):
            y_mid = header_bottom - ROW_H * i - ROW_H / 2
            self.text(row.designator, xs[0] + 1.5, y_mid, fit=COLUMNS[0] - 3.0)
            if row.is_heading:
                self.centered(row.name, xs[1], y_mid - ROW_H / 2, COLUMNS[1], ROW_H)
            else:
                self.text(row.name, xs[1] + 2.0, y_mid, fit=COLUMNS[1] - 4.0)
            if row.quantity is not None:
                self.centered(str(row.quantity), xs[2], y_mid - ROW_H / 2, COLUMNS[2], ROW_H)
            self.text(row.note, xs[3] + 2.0, y_mid, fit=COLUMNS[3] - 4.0)

    def change_labels(self, y: float):
        """The 'Изм. Лист № докум. Подп. Дата' row shared by forms 2 and 2a."""
        x = LEFT
        for w, label in zip(CHANGE_WIDTHS, CHANGE_LABELS):
            self.centered(label, x, y, w, 5.0, SMALL_H)
            x += w

    def form2(self, title: TitleBlock, sheets: int):
        y0 = MARGIN
        self.rect(LEFT, y0, 185.0, FORM2_H)

        # Left part, bottom to top: 5 signature rows, the column-label row, 2 change rows.
        # The 7 mm 'Изм.' column exists only above the signatures, where roles take 17 mm.
        self.line(LEFT + 7.0, y0 + 25.0, LEFT + 7.0, y0 + FORM2_H, THICK)
        for x in (17.0, 40.0, 55.0, 65.0):
            self.line(LEFT + x, y0, LEFT + x, y0 + FORM2_H, THICK)
        for r in range(1, 8):
            self.line(LEFT, y0 + r * 5.0, LEFT + 65.0, y0 + r * 5.0, THICK if r in (5, 6) else THIN)
        self.change_labels(y0 + 25.0)
        signatures = [
            ("Разраб.", title.developer),
            ("Пров.", title.checker),
            ("Т. контр.", title.tech_control),
            ("Н. контр.", title.norm_control),
            ("Утв.", title.approver),
        ]
        for i, (role, person) in enumerate(signatures):
            y = y0 + 20.0 - i * 5.0
            self.text(role, LEFT + 1.0, y + 2.5, SMALL_H)
            self.text(person, LEFT + 18.0, y + 2.5, SMALL_H)

        # Right part: designation (graph 2), name (graph 1), litera / sheet / sheets, organization.
        self.line(LEFT + 65.0, y0 + 25.0, LEFT + 185.0, y0 + 25.0, THICK)
        self.centered(title.code, LEFT + 65.0, y0 + 25.0, 120.0, 15.0, 5.0)
        self.line(LEFT + 135.0, y0, LEFT + 135.0, y0 + 25.0, THICK)
        self.centered(title.title, LEFT + 65.0, y0 + 12.5, 70.0, 12.5, TEXT_H)
        self.centered(title.document_name, LEFT + 65.0, y0, 70.0, 12.5, TEXT_H)

        self.line(LEFT + 135.0, y0 + 20.0, LEFT + 185.0, y0 + 20.0, THICK)
        self.line(LEFT + 135.0, y0 + 15.0, LEFT + 185.0, y0 + 15.0, THICK)
        for x in (150.0, 165.0):
            self.line(LEFT + x, y0 + 15.0, LEFT + x, y0 + 25.0, THICK)
        for x in (140.0, 145.0):
            self.line(LEFT + x, y0 + 15.0, LEFT + x, y0 + 20.0, THIN)
        self.centered("Лит.", LEFT + 135.0, y0 + 20.0, 15.0, 5.0, SMALL_H)
        self.centered("Лист", LEFT + 150.0, y0 + 20.0, 15.0, 5.0, SMALL_H)
        self.centered("Листов", LEFT + 165.0, y0 + 20.0, 20.0, 5.0, SMALL_H)
        for i, letter in enumerate(title.litera[:3]):
            self.centered(letter, LEFT + 135.0 + i * 5.0, y0 + 15.0, 5.0, 5.0, SMALL_H)
        if sheets > 1:
            self.centered("1", LEFT + 150.0, y0 + 15.0, 15.0, 5.0, SMALL_H)
        self.centered(str(sheets), LEFT + 165.0, y0 + 15.0, 20.0, 5.0, SMALL_H)
        self.centered(title.organization, LEFT + 135.0, y0, 50.0, 15.0, TEXT_H)

    def form2a(self, title: TitleBlock, sheet_no: int):
        y0 = MARGIN
        self.rect(LEFT, y0, 185.0, FORM2A_H)
        x = LEFT
        for w in CHANGE_WIDTHS:
            x += w
            self.line(x, y0, x, y0 + FORM2A_H, THICK)
        for r in (1, 2):
            self.line(LEFT, y0 + r * 5.0, LEFT + 65.0, y0 + r * 5.0, THICK if r == 1 else THIN)
        self.change_labels(y0)

        self.line(LEFT + 175.0, y0, LEFT + 175.0, y0 + FORM2A_H, THICK)
        self.line(LEFT + 175.0, y0 + 8.0, LEFT + 185.0, y0 + 8.0, THICK)
        self.centered(title.code, LEFT + 65.0, y0, 110.0, FORM2A_H, 5.0)
        self.centered("Лист", LEFT + 175.0, y0 + 8.0, 10.0, 7.0, SMALL_H)
        self.centered(str(sheet_no), LEFT + 175.0, y0, 10.0, 8.0, TEXT_H)
