import pytest

from eskd_bom.models import BLANK, Component, Row
from eskd_bom.rules import build_rows, paginate, wrap_rows

R10K = "Резистор 10 кОм"


def designators(rows: list[Row]) -> list[str]:
    return [r.designator for r in rows if r.designator]


@pytest.mark.parametrize("bad", ["r1", "R", "1R", "R1a", "РЕЗ1", "ABCD1"])
def test_component_rejects_bad_designators(bad):
    with pytest.raises(ValueError):
        Component(bad, "Резистор")


def test_component_rejects_empty_name():
    with pytest.raises(ValueError):
        Component("R1", "  ")


def test_three_identical_neighbours_become_a_range():
    rows = build_rows([Component(f"R{i}", R10K) for i in (1, 2, 3)])
    assert rows == [Row(name="Резисторы", is_heading=True), Row("R1...R3", R10K, 3)]


def test_two_identical_neighbours_are_listed_with_a_comma():
    rows = build_rows([Component("C1", "Конденсатор 0,1 мкФ"), Component("C2", "Конденсатор 0,1 мкФ")])
    assert designators(rows) == ["C1, C2"]
    assert rows[-1].quantity == 2


def test_a_gap_in_numbering_breaks_the_range():
    rows = build_rows([Component("R1", R10K), Component("R2", R10K), Component("R4", R10K)])
    assert designators(rows) == ["R1, R2", "R4"]


def test_a_different_note_breaks_the_range():
    rows = build_rows([Component("R1", R10K), Component("R2", R10K, "Подбирают при настройке"), Component("R3", R10K)])
    assert designators(rows) == ["R1", "R2", "R3"]


def test_numbers_sort_numerically_not_as_text():
    rows = build_rows([Component("R10", "Резистор 1 кОм"), Component("R2", R10K), Component("R1", "Резистор 2 кОм")])
    assert designators(rows) == ["R1", "R2", "R10"]


def test_groups_follow_letter_code_order_with_a_blank_row_between():
    rows = build_rows([Component("R1", R10K), Component("C1", "Конденсатор"), Component("DA1", "Микросхема LM358")])
    assert [r.designator for r in rows] == ["C1", "", "DA1", "", "R1"]
    assert rows[1] == BLANK


def test_single_element_gets_no_group_heading():
    rows = build_rows([Component("VT1", "Транзистор SI2302")])
    assert not any(r.is_heading for r in rows)


def test_unknown_letter_code_gets_no_heading():
    rows = build_rows([Component("XYZ1", "Изделие"), Component("XYZ2", "Изделие другое")])
    assert not any(r.is_heading for r in rows)


def test_duplicate_designator_is_rejected():
    with pytest.raises(ValueError, match="R1"):
        build_rows([Component("R1", R10K), Component("R1", "Резистор 1 кОм")])


def test_long_name_and_note_wrap_onto_continuation_rows():
    row = Row("R9", "Резистор очень длинное наименование", 1, "Подбирают при настройке")
    wrapped = wrap_rows([row], name_chars=20, note_chars=12)

    assert [r.name for r in wrapped] == ["Резистор очень", "длинное наименование", ""]
    assert [r.note for r in wrapped] == ["Подбирают", "при", "настройке"]
    assert wrapped[0].designator == "R9" and wrapped[0].quantity == 1
    assert all(r.designator == "" and r.quantity is None for r in wrapped[1:])


def test_first_sheet_holds_29_rows_and_next_sheets_32():
    rows = [Row(f"R{i}", R10K, 1) for i in range(1, 62)]
    pages = paginate(rows)
    assert [len(p) for p in pages] == [29, 32]


def test_heading_never_ends_a_sheet():
    rows = [Row(f"C{i}", "Конденсатор", 1) for i in range(1, 28)] + [BLANK, Row(name="Резисторы", is_heading=True)]
    rows += [Row(f"R{i}", R10K, 1) for i in range(1, 4)]
    first, second = paginate(rows)

    assert first[-1].designator == "C27"
    assert second[0].is_heading


def test_empty_list_still_gives_one_sheet():
    assert paginate([]) == [[]]
