import argparse
import sys
from pathlib import Path

from eskd_bom import drawing, rules
from eskd_bom.models import Component, TitleBlock
from eskd_bom.reader import read_components
from eskd_bom.tables import read_csv, write_table


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eskd-bom", description="Parts lists (перечень элементов) from AutoCAD schematics, to ESKD."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    extract = commands.add_parser("extract", help="Read components from a schematic DXF into CSV or Excel")
    extract.add_argument("drawing", type=Path)
    extract.add_argument("-o", "--output", type=Path, required=True, help=".csv or .xlsx")

    generate = commands.add_parser("generate", help="Draw a parts list DXF from a CSV of components")
    generate.add_argument("components", type=Path, help="CSV with Designator, Name, Note")
    _add_sheet_options(generate)

    build = commands.add_parser("build", help="Schematic DXF straight to a parts list DXF")
    build.add_argument("drawing", type=Path)
    _add_sheet_options(build)

    args = parser.parse_args()
    try:
        if args.command == "extract":
            components = _read_drawing(args.drawing)
            write_table(components, args.output)
            print(f"{len(components)} components -> {args.output}")
        else:
            components = _read_drawing(args.drawing) if args.command == "build" else read_csv(args.components)
            _generate(components, args)
    except (ValueError, OSError) as error:
        sys.exit(f"error: {error}")


def _add_sheet_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .dxf")
    parser.add_argument("--code", required=True, help="Document designation, e.g. АБВГ.468157.001ПЭ3")
    parser.add_argument("--title", required=True, help="Product name for graph 1")
    parser.add_argument("--organization", default="")
    parser.add_argument("--developer", default="")
    parser.add_argument("--checker", default="")
    parser.add_argument("--norm-control", default="")
    parser.add_argument("--approver", default="")
    parser.add_argument("--litera", default="")
    parser.add_argument("--preview", type=Path, help="Also save a PNG preview of the sheets")


def _read_drawing(path: Path) -> list[Component]:
    result = read_components(path)
    if result.skipped_blocks:
        names = sorted(set(result.skipped_blocks))
        print(f"skipped {len(result.skipped_blocks)} blocks without a designator: {', '.join(names)}")
    if not result.components:
        raise ValueError(f"no components found in {path.name}")
    return result.components


def _generate(components: list[Component], args: argparse.Namespace) -> None:
    title = TitleBlock(
        code=args.code,
        title=args.title,
        organization=args.organization,
        developer=args.developer,
        checker=args.checker,
        norm_control=args.norm_control,
        approver=args.approver,
        litera=args.litera,
    )
    rows = rules.wrap_rows(rules.build_rows(components), drawing.NAME_CHARS, drawing.NOTE_CHARS)
    pages = rules.paginate(rows)
    drawing.render(pages, title, args.output)
    print(f"{len(components)} components, {len(rows)} rows, {len(pages)} sheet(s) -> {args.output}")

    if args.preview:
        from eskd_bom.preview import save_png

        save_png(args.output, args.preview)
        print(f"preview -> {args.preview}")


if __name__ == "__main__":
    main()
