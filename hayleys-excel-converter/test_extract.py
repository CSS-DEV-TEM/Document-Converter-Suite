from pathlib import Path
from collections import defaultdict
from decimal import Decimal

from app.extractor import extract_pdf, display_number


pdf_path = (
    Path(__file__).resolve().parent
    / "samples"
    / "227-2966.pdf"
)

result = extract_pdf(pdf_path)

print(f"\nFile: {pdf_path.name}")
print(f"Roll rows: {len(result.rows)}")
print(f"Subtotal sections: {len(result.checks)}")
print(f"Passed sections: {sum(c.passed for c in result.checks)}")
print(f"Errors: {len(result.errors)}")
print(f"Overall: {'PASS' if result.passed else 'FAIL'}")

print("\nFIRST 5 ROWS")

for row in result.rows[:5]:
    print(
        f"PO: {row.purchase_order} | "
        f"Invoice: {row.invoice} | "
        f"Batch: {row.batch} | "
        f"Item: {row.item} | "
        f"No: {row.vendor_roll} | "
        f"Qty: {display_number(row.quantity)} {row.unit}"
    )

print("\nBATCH VALIDATION")

for check in result.checks:
    status = "PASS" if check.passed else "FAIL"

    print(
        f"{status} | "
        f"Page: {check.page} | "
        f"Invoice: {check.invoice} | "
        f"Batch: {check.batch} | "
        f"Rolls: {check.actual_count}/{check.expected_count} | "
        f"PDF: {display_number(check.expected_quantity)} | "
        f"Extracted: {display_number(check.actual_quantity)} | "
        f"Difference: {display_number(check.difference)} "
        f"{check.unit}"
    )

totals = defaultdict(lambda: Decimal("0"))

for row in result.rows:
    totals[row.unit] += row.quantity

print("\nTOTALS BY UNIT")

for unit, quantity in sorted(totals.items()):
    print(f"{unit}: {display_number(quantity)}")

if result.errors:
    print("\nERROR DETAILS")

    for error in result.errors:
        print(error)