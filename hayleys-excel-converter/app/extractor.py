from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import re

import pdfplumber


@dataclass
class Roll:
    source_file: str
    page: int
    delivery: str
    purchase_order: str
    invoice: str
    batch: str
    item: str
    vendor_roll: str
    quantity: Decimal
    unit: str


@dataclass
class BatchCheck:
    source_file: str
    page: int
    delivery: str
    invoice: str
    batch: str
    unit: str
    expected_count: int
    actual_count: int
    expected_quantity: Decimal
    actual_quantity: Decimal

    @property
    def difference(self):
        return self.actual_quantity - self.expected_quantity

    @property
    def passed(self):
        return (
            self.expected_count == self.actual_count
            and self.difference == 0
        )


@dataclass
class Extraction:
    rows: list[Roll]
    checks: list[BatchCheck]
    errors: list[str]

    @property
    def passed(self):
        return (
            bool(self.rows)
            and bool(self.checks)
            and not self.errors
            and all(check.passed for check in self.checks)
        )


def display_number(value):
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def extract_pdf(file_path):
    path = Path(file_path)
    result = Extraction(rows=[], checks=[], errors=[])

    delivery = ""
    purchase_order = ""
    invoice = ""
    batch = ""
    pending = []

    def report(page, message):
        result.errors.append(
            f"{path.name} | Page {page} | {message}"
        )

    def check_unclosed():
        if pending:
            first = pending[0]
            report(
                first.page,
                f"Batch {first.batch}: "
                f"{len(pending)} rows have no closing subtotal.",
            )
            pending.clear()

    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                report(
                    page_number,
                    "No readable text. This page may require OCR.",
                )
                continue

            match = re.search(
                r"DeliveryNo\s*:\s*(\S+)",
                text,
            )

            if not match:
                report(page_number, "Delivery number was not found.")
                continue

            current_delivery = match.group(1)

            if current_delivery != delivery:
                check_unclosed()
                delivery = current_delivery
                purchase_order = ""
                invoice = ""
                batch = ""

            words = page.extract_words()

            headers = [
                word for word in words
                if word["text"] == "Cus.PO"
            ]

            if not headers:
                # The sample contains signature-only pages.
                if "AuthorizedSignature" in text:
                    continue

                report(page_number, "Packing-list table header not found.")
                continue

            scale = page.width / 842
            body_top = headers[0]["top"] + 10

            def cell(left, right, top, bottom):
                selected = [
                    word for word in words
                    if left * scale <= word["x0"] < right * scale
                    and top <= word["top"] < bottom
                ]
                selected.sort(
                    key=lambda word: (round(word["top"], 1), word["x0"])
                )
                return "".join(word["text"] for word in selected)

            quantity_words = [
                word for word in words
                if 681 * scale <= word["x0"] < 754 * scale
                and word["top"] > body_top
            ]

            anchors = []

            for word in quantity_words:
                if re.fullmatch(
                    r"[\d,]+(?:\.\d+)?(?:YD|M)",
                    word["text"],
                ):
                    anchors.append(word)
                else:
                    report(
                        page_number,
                        f"Unrecognized quantity: {word['text']}",
                    )

            anchors.sort(key=lambda word: word["top"])

            if not anchors:
                report(page_number, "No quantity rows found.")
                continue

            previous_top = body_top

            for index, anchor in enumerate(anchors):
                y = anchor["top"]

                next_top = (
                    anchors[index + 1]["top"] - 2
                    if index + 1 < len(anchors)
                    else y + 22
                )

                new_po = cell(20, 54, previous_top, y + 2)
                new_invoice = cell(54, 103, previous_top, y + 2)

                if new_po:
                    purchase_order = new_po

                if new_invoice:
                    invoice = new_invoice

                label = cell(480, 524, y - 2, next_top)
                roll_cell = cell(524, 588, y - 2, y + 2)
                vendor_roll = cell(588, 610, y - 2, y + 2)

                quantity_match = re.fullmatch(
                    r"([\d,]+(?:\.\d+)?)(YD|M)",
                    anchor["text"],
                )

                quantity = Decimal(
                    quantity_match.group(1).replace(",", "")
                )
                unit = quantity_match.group(2)

                previous_top = y + 3

                if label == "SubTot":
                    if not pending:
                        report(
                            page_number,
                            "Subtotal found without preceding roll rows.",
                        )
                        continue

                    try:
                        expected_count = int(roll_cell)
                    except ValueError:
                        report(
                            page_number,
                            f"Invalid subtotal roll count: {roll_cell}",
                        )
                        pending.clear()
                        continue

                    first = pending[0]

                    if any(
                        (
                            row.delivery,
                            row.purchase_order,
                            row.invoice,
                            row.batch,
                            row.unit,
                        )
                        != (
                            first.delivery,
                            first.purchase_order,
                            first.invoice,
                            first.batch,
                            first.unit,
                        )
                        for row in pending
                    ):
                        report(
                            page_number,
                            "One subtotal section contains mixed "
                            "PO, invoice, batch or unit values.",
                        )

                    if unit != first.unit:
                        report(
                            page_number,
                            "Subtotal unit differs from roll quantity unit.",
                        )

                    result.checks.append(
                        BatchCheck(
                            source_file=path.name,
                            page=page_number,
                            delivery=first.delivery,
                            invoice=first.invoice,
                            batch=first.batch,
                            unit=unit,
                            expected_count=expected_count,
                            actual_count=len(pending),
                            expected_quantity=quantity,
                            actual_quantity=sum(
                                (row.quantity for row in pending),
                                Decimal("0"),
                            ),
                        )
                    )

                    pending.clear()
                    continue

                summary_labels = {"ItemTotal", "TOTAL"}

                is_summary_row = any(
                    word["text"] in summary_labels
                    and 480 * scale <= word["x0"] < 588 * scale
                    and y - 2 <= word["top"] < y + 2
                    for word in words
                )

                if is_summary_row:
                    # Detect the original PDF label before cell text
                    # joins TOTAL and its adjacent roll count.
                    continue

                if label:
                    batch = label

                required = {
                    "Purchase order": purchase_order,
                    "Invoice": invoice,
                    "Batch": batch,
                    "Roll number": roll_cell,
                    "Vendor roll number": vendor_roll,
                }

                missing = [
                    name for name, value in required.items()
                    if not value
                ]

                if missing:
                    report(
                        page_number,
                        "Missing values: " + ", ".join(missing),
                    )

                row = Roll(
                    source_file=path.name,
                    page=page_number,
                    delivery=delivery,
                    purchase_order=purchase_order,
                    invoice=invoice,
                    batch=batch,
                    item=roll_cell,
                    vendor_roll=vendor_roll,
                    quantity=quantity,
                    unit=unit,
                )

                result.rows.append(row)
                pending.append(row)

    check_unclosed()

    if not result.rows:
        result.errors.append(f"{path.name} | No roll data extracted.")

    return result