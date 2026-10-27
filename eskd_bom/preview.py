from pathlib import Path

import ezdxf
from ezdxf.addons.drawing import matplotlib as dxf_matplotlib


def save_png(dxf_path: Path, png_path: Path, dpi: int = 200) -> None:
    """Render model space of a DXF file to PNG, black on white, to check a sheet without AutoCAD."""
    doc = ezdxf.readfile(dxf_path)
    dxf_matplotlib.qsave(doc.modelspace(), str(png_path), dpi=dpi, bg="#FFFFFF", fg="#000000")
