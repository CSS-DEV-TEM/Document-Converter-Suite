from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class ItemRow:
    invoice: str
    lot: str
    package_no: int
    carton_code: str
    meters: Decimal
    source_page: int


@dataclass
class ParsedDelivery:
    source_path: Path
    file_hash: str
    invoice: str
    lot: str
    rows: list[ItemRow] = field(default_factory=list)

    # Read from the PDF's package-detail section.
    expected_meters: Decimal | None = None
    expected_package_count: int | None = None
    expected_package_numbers: set[int] | None = None

    # Set only when the parser identifies the section boundary.
    package_section_complete: bool = False

    # Missing text, incomplete items, unsupported layouts, etc.
    extraction_errors: list[str] = field(default_factory=list)

    @property
    def total_meters(self) -> Decimal:
        return sum(
            (row.meters for row in self.rows),
            start=Decimal("0"),
        )

    @property
    def package_numbers(self) -> set[int]:
        return {row.package_no for row in self.rows}


@dataclass
class ValidationResult:
    delivery: ParsedDelivery
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass
class BatchResult:
    results: list[ValidationResult] = field(default_factory=list)
    batch_errors: list[str] = field(default_factory=list)

    @property
    def can_export(self) -> bool:
        return (
            bool(self.results)
            and not self.batch_errors
            and all(result.passed for result in self.results)
        )

    @property
    def validated_rows(self) -> list[ItemRow]:
        return [
            row
            for result in self.results
            if result.passed
            for row in result.delivery.rows
        ]

    @property
    def total_meters(self) -> Decimal:
        return sum(
            (row.meters for row in self.validated_rows),
            start=Decimal("0"),
        )