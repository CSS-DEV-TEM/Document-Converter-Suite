from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pdfplumber


ZERO = Decimal("0")
NUMBER = r"\d[\d,]*(?:\.\d+)?"

INVOICE_PATTERN = re.compile(
    r"\bInvoice\s*(?:no\.?\s*:?\s*)?:?\s*(SIN[\w-]+)",
    re.IGNORECASE,
)

ORDER_PATTERN = re.compile(
    r"P/I\s+NO\.\s*(\S+)\s*,\s*CUSTOMER\s+P/O\s+NO\.\s*(\S+)",
    re.IGNORECASE,
)

ITEM_PATTERN = re.compile(r"RT[A-Za-z0-9_]+")

ROW_PATTERN = re.compile(
    rf"^(\S+)\s+COL:\s*(.*?)\s+({NUMBER})\s+YDS\s+(.+)$",
    re.IGNORECASE,
)

TOTAL_PATTERN = re.compile(
    rf"\bTOTAL\s+([\d,]+)\s+ROLL\(S\)\s+({NUMBER})\s*YDS",
    re.IGNORECASE,
)


def decimal_value(value: str) -> Decimal:
    return Decimal(value.replace(",", ""))


def display_number(value: Decimal) -> str:
    return format(value.normalize(), "f")


@dataclass
class Roll:
    invoice: str
    purchase_order: str
    item: str
    color: str
    lot: str
    package: str
    quantity: Decimal
    net_weight: Decimal | None
    gross_weight: Decimal | None
    source_pages: list[int] = field(default_factory=list)
    foc_quantity: Decimal = ZERO

    @property
    def foc_note(self) -> str:
        if not self.foc_quantity:
            return ""
        return f"FOC-{display_number(self.foc_quantity)}"

    @property
    def identity(self) -> tuple[str, ...]:
        return (
            self.invoice,
            self.purchase_order,
            self.item,
            self.color,
            self.lot,
            self.package,
        )


@dataclass
class ExtractionResult:
    rows: list[Roll]
    page_count: int
    raw_row_count: int
    checked_invoices: list[str]
    warnings: list[str]

    @property
    def total_quantity(self) -> Decimal:
        return sum((row.quantity for row in self.rows), ZERO)

    @property
    def total_net_weight(self) -> Decimal:
        return sum(
            (
                row.net_weight
                for row in self.rows
                if row.net_weight is not None
            ),
            ZERO,
        )

    @property
    def total_gross_weight(self) -> Decimal:
        return sum(
            (
                row.gross_weight
                for row in self.rows
                if row.gross_weight is not None
            ),
            ZERO,
        )


def combine_packages(rows: list[Roll]) -> list[Roll]:
    combined: dict[tuple[str, ...], Roll] = {}

    for row in rows:
        key = row.identity

        if key not in combined:
            combined[key] = row
            continue

        existing = combined[key]
        existing.quantity += row.quantity
        existing.foc_quantity += row.foc_quantity

        if row.net_weight is not None:
            existing.net_weight = (
                existing.net_weight or ZERO
            ) + row.net_weight

        if row.gross_weight is not None:
            existing.gross_weight = (
                existing.gross_weight or ZERO
            ) + row.gross_weight

        for page in row.source_pages:
            if page not in existing.source_pages:
                existing.source_pages.append(page)

    return list(combined.values())


def extract_pdf(pdf_path: str | Path) -> ExtractionResult:
    pdf_path = Path(pdf_path)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    raw_rows: list[Roll] = []
    warnings: list[str] = []
    printed_totals: dict[str, tuple[int, Decimal]] = {}

    invoice = ""
    purchase_order = ""
    item = ""
    previous_row: Roll | None = None

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                if page.images:
                    raise ValueError(
                        f"Page {page_number}: image-only content found. "
                        "OCR is required; extraction stopped to avoid "
                        "silently skipping data."
                    )
                continue

            for original_line in text.splitlines():
                line = original_line.strip()

                if not line:
                    continue

                match = INVOICE_PATTERN.search(line)
                if match:
                    new_invoice = match.group(1)

                    if new_invoice != invoice:
                        purchase_order = ""
                        item = ""

                    invoice = new_invoice
                    previous_row = None
                    continue

                match = ORDER_PATTERN.search(line)
                if match:
                    # P/I identifies a section. The export invoice is SIN.
                    purchase_order = match.group(2)
                    previous_row = None
                    continue

                if ITEM_PATTERN.fullmatch(line):
                    item = line
                    previous_row = None
                    continue

                match = ROW_PATTERN.match(line)
                if match:
                    if not invoice or not purchase_order or not item:
                        raise ValueError(
                            f"Page {page_number}: a package row has "
                            "missing invoice, purchase order or item."
                        )

                    package, color, quantity_text, tail = match.groups()
                    fields = tail.split()

                    if len(fields) == 3:
                        net_weight = decimal_value(fields[0])
                        gross_weight = decimal_value(fields[1])
                        lot = fields[2]

                        if net_weight < ZERO or gross_weight < net_weight:
                            raise ValueError(
                                f"Page {page_number}, package {package}: "
                                "invalid N.W/G.W values."
                            )

                    elif len(fields) == 1:
                        # The confirmed sample uses these as FOC rows.
                        net_weight = None
                        gross_weight = None
                        lot = fields[0]

                    else:
                        raise ValueError(
                            f"Page {page_number}: unrecognized row:\n{line}"
                        )

                    quantity = decimal_value(quantity_text)

                    previous_row = Roll(
                        invoice=invoice,
                        purchase_order=purchase_order,
                        item=item,
                        color=color.strip(),
                        lot=lot,
                        package=package,
                        quantity=quantity,
                        net_weight=net_weight,
                        gross_weight=gross_weight,
                        source_pages=[page_number],
                        foc_quantity=(
                            quantity if net_weight is None else ZERO
                        ),
                    )

                    raw_rows.append(previous_row)
                    continue

                if "COL:" in line.upper():
                    raise ValueError(
                        f"Page {page_number}: unsupported package row:\n"
                        f"{line}"
                    )

                # Wrapped color names in the supplied STANTEX layout.
                # Example: '... BLUE X-' followed by 'DYE'.
                if previous_row is not None and (
                    "X-DYE" in line or line == "DYE"
                ):
                    if not previous_row.color.endswith(line):
                        separator = (
                            "" if previous_row.color.endswith("-") else " "
                        )
                        previous_row.color += separator + line
                    continue

                match = TOTAL_PATTERN.search(line)
                if match:
                    if not invoice:
                        raise ValueError(
                            f"Page {page_number}: total has no invoice."
                        )

                    total = (
                        int(match.group(1).replace(",", "")),
                        decimal_value(match.group(2)),
                    )

                    if (
                        invoice in printed_totals
                        and printed_totals[invoice] != total
                    ):
                        raise ValueError(
                            f"{invoice}: conflicting printed totals."
                        )

                    printed_totals[invoice] = total
                    previous_row = None

    if not raw_rows:
        raise ValueError(
            "No supported packing-list rows were found in this PDF."
        )

    raw_row_count = len(raw_rows)
    rows = combine_packages(raw_rows)
    checked_invoices: list[str] = []

    for invoice_number in dict.fromkeys(row.invoice for row in rows):
        invoice_rows = [
            row for row in rows if row.invoice == invoice_number
        ]

        if invoice_number not in printed_totals:
            warnings.append(
                f"{invoice_number}: printed total not found. "
                "Manual review is required."
            )
            continue

        expected_count, expected_quantity = printed_totals[invoice_number]
        actual_quantity = sum(
            (row.quantity for row in invoice_rows), ZERO
        )

        if (
            len(invoice_rows) != expected_count
            or actual_quantity != expected_quantity
        ):
            raise ValueError(
                f"{invoice_number}: totals do not match.\n"
                f"PDF: {expected_count} rolls / "
                f"{expected_quantity} YDS\n"
                f"Extracted: {len(invoice_rows)} rolls / "
                f"{actual_quantity} YDS"
            )

        checked_invoices.append(invoice_number)

    for row in rows:
        if row.net_weight is None or row.gross_weight is None:
            warnings.append(
                f"{row.invoice}, PO {row.purchase_order}, "
                f"package {row.package}: no weighted base row "
                "was found. N.W/G.W remain blank."
            )

    return ExtractionResult(
        rows=rows,
        page_count=page_count,
        raw_row_count=raw_row_count,
        checked_invoices=checked_invoices,
        warnings=warnings,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a STANTEX packing-list PDF."
    )
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()

    try:
        result = extract_pdf(args.pdf)
    except Exception as error:
        print(f"\nERROR: {error}")
        return 1

    print("\nSTANTEX PDF CONVERTER")
    print("-" * 52)
    print(f"PDF pages       : {result.page_count}")
    print(f"Source rows     : {result.raw_row_count}")
    print(f"Combined rolls  : {len(result.rows)}")
    print(f"Total quantity  : {result.total_quantity:,.0f} YDS")
    print(f"Total N.W       : {result.total_net_weight:,.2f} KG")
    print(f"Total G.W       : {result.total_gross_weight:,.2f} KG")

    print("\nFOC packages")
    print("-" * 52)

    for row in result.rows:
        if row.foc_quantity:
            print(
                f"{row.package:<6} | "
                f"PO {row.purchase_order} | "
                f"Qty {display_number(row.quantity):>4} | "
                f"{row.foc_note}"
            )

    print("\nValidation")
    for invoice_number in result.checked_invoices:
        print(f"PASS: {invoice_number} - roll count and quantity match.")

    for warning in result.warnings:
        print(f"WARNING: {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())