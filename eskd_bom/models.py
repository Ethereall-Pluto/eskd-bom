import re
from dataclasses import dataclass

DESIGNATOR = re.compile(r"^([A-Z]{1,3})(\d+)$")


@dataclass(frozen=True)
class Component:
    """One element of the circuit: its reference designator (GOST 2.710), name and note."""

    designator: str
    name: str
    note: str = ""

    def __post_init__(self) -> None:
        if not DESIGNATOR.match(self.designator):
            raise ValueError(
                f"designator {self.designator!r} must be 1-3 Latin capitals and a number, like R1 or VD12"
            )
        if not self.name.strip():
            raise ValueError(f"{self.designator}: name must not be empty")

    @property
    def prefix(self) -> str:
        return DESIGNATOR.match(self.designator).group(1)

    @property
    def number(self) -> int:
        return int(DESIGNATOR.match(self.designator).group(2))


@dataclass(frozen=True)
class Row:
    """One 8 mm row of the parts list. A heading or blank row has no designator and no quantity."""

    designator: str = ""
    name: str = ""
    quantity: int | None = None
    note: str = ""
    is_heading: bool = False


BLANK = Row()


@dataclass(frozen=True)
class TitleBlock:
    """Contents of the title block (GOST 2.104, forms 2 and 2a)."""

    code: str
    title: str
    document_name: str = "Перечень элементов"
    organization: str = ""
    developer: str = ""
    checker: str = ""
    tech_control: str = ""
    norm_control: str = ""
    approver: str = ""
    litera: str = ""
