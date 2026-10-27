"""Creates examples/sample_schematic.dxf: a made-up control board drawn the way AutoCAD users do it,
with every element as a block reference carrying REF / NAME / NOTE attributes.

Run from the repository root:  python examples/make_sample_schematic.py
"""

from pathlib import Path

import ezdxf

PARTS = [
    ("DA1", "Микросхема LM358DR2G", ""),
    ("RK1", "Терморезистор NCP18XH103F03RB 10 кОм", ""),
    ("VT1", "Транзистор SI2302CDS", ""),
    ("VT2", "Транзистор SI2302CDS", ""),
    ("VD1", "Диод 1N4148WS", ""),
    ("VD2", "Диод 1N4148WS", ""),
    ("VD3", "Стабилитрон BZX84C12", ""),
    ("HL1", "Светодиод KP-1608SGC зелёный", ""),
    ("HL2", "Светодиод KP-1608SRC красный", ""),
    ("K1", "Реле HF46F-G/12-HS1", ""),
    ("FU1", "Предохранитель 0466001.NR 1 А", ""),
    ("SB1", "Кнопка TS-1187A-B-A-B", ""),
    ("XP1", "Вилка PLS-2", ""),
    ("XP2", "Вилка PLS-3", ""),
    ("C1", "Конденсатор GRM188R71H104KA93D 0,1 мкФ", ""),
    ("C2", "Конденсатор GRM188R71H104KA93D 0,1 мкФ", ""),
    ("C3", "Конденсатор GRM188R71H104KA93D 0,1 мкФ", ""),
    ("C4", "Конденсатор GRM21BR61E106KA73L 10 мкФ", ""),
    ("C5", "Конденсатор GRM21BR61E106KA73L 10 мкФ", ""),
    ("C6", "Конденсатор EEE-FK1E101P 100 мкФ x 25 В", ""),
    ("R1", "Резистор RC0603FR-0710KL 10 кОм ±1%", ""),
    ("R2", "Резистор RC0603FR-0710KL 10 кОм ±1%", ""),
    ("R3", "Резистор RC0603FR-0710KL 10 кОм ±1%", ""),
    ("R4", "Резистор RC0603FR-07100KL 100 кОм ±1%", ""),
    ("R5", "Резистор RC0603FR-071KL 1 кОм ±1%", ""),
    ("R6", "Резистор RC0603FR-071KL 1 кОм ±1%", ""),
    ("R7", "Резистор RC0603FR-07470RL 470 Ом ±1%", ""),
    ("R8", "Резистор RC0603FR-07470RL 470 Ом ±1%", ""),
    ("R9", "Резистор RC0603FR-074K7L 4,7 кОм ±1%", "Подбирают при настройке"),
    ("R10", "Резистор RC0603FR-0710RL 10 Ом ±1%", ""),
    ("R11", "Резистор RC0603FR-0710KL 10 кОм ±1%", ""),
    ("R12", "Резистор RC0603FR-0710KL 10 кОм ±1%", ""),
    ("R13", "Резистор RC1206FR-070R1L 0,1 Ом ±1%", "Шунт тока"),
    ("R14", "Резистор RC0603FR-07100KL 100 кОм ±1%", ""),
    ("ZQ1", "Резонатор кварцевый HC-49S 8 МГц", ""),
]


def main() -> None:
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.MM

    element = doc.blocks.new("ELEMENT")
    element.add_lwpolyline([(0, 0), (12, 0), (12, 5), (0, 5)], close=True)
    element.add_attdef("REF", insert=(0, 6), height=2.5)
    element.add_attdef("NAME", insert=(0, -3.5), height=1.8)
    element.add_attdef("NOTE", insert=(0, -6), height=1.8)

    title = doc.blocks.new("LOGO")  # a block with no designator: the reader must skip it
    title.add_circle((0, 0), 5)

    msp = doc.modelspace()
    for i, (ref, name, note) in enumerate(PARTS):
        x, y = (i % 7) * 40, -(i // 7) * 25
        ref_block = msp.add_blockref("ELEMENT", (x, y))
        ref_block.add_auto_attribs({"REF": ref, "NAME": name, "NOTE": note})
    msp.add_blockref("LOGO", (-20, 20))

    out = Path(__file__).with_name("sample_schematic.dxf")
    doc.saveas(out)
    print(f"{len(PARTS)} elements -> {out}")


if __name__ == "__main__":
    main()
