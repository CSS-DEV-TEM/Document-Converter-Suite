import re
from decimal import Decimal

from app.models import ParsedDelivery, ValidationResult


def validate_delivery(
    delivery: ParsedDelivery,
) -> ValidationResult:
    errors = list(delivery.extraction_errors)

    def add_error(message: str) -> None:
        if message not in errors:
            errors.append(message)

    if not re.fullmatch(r"ME\d+", delivery.invoice.strip()):
        add_error(
            "Missing or invalid ME-number invoice in the PDF header."
        )

    if not delivery.lot.strip():
        add_error("LOT number is missing.")

    if not delivery.rows:
        add_error("No package item rows were extracted.")

    if not delivery.package_section_complete:
        add_error(
            "The end of the package-detail section "
            "could not be confirmed."
        )

    valid_meter_values = True

    for index, row in enumerate(delivery.rows, start=1):
        location = (
            f"Row {index}, PDF page {row.source_page}, "
            f"package {row.package_no}"
        )

        if row.invoice != delivery.invoice:
            add_error(f"{location}: invoice mismatch.")

        if row.lot != delivery.lot:
            add_error(f"{location}: LOT mismatch.")

        if row.package_no <= 0:
            add_error(f"{location}: invalid package number.")

        if not row.carton_code.strip():
            add_error(f"{location}: carton code is missing.")

        if (
            not isinstance(row.meters, Decimal)
            or not row.meters.is_finite()
        ):
            valid_meter_values = False
            add_error(f"{location}: invalid meters value.")
        elif row.meters <= 0:
            add_error(f"{location}: meters must be greater than zero.")

    expected_total = delivery.expected_meters

    if expected_total is None:
        add_error("The package-section meters total was not found.")
    elif (
        not isinstance(expected_total, Decimal)
        or not expected_total.is_finite()
        or expected_total <= 0
    ):
        add_error("The PDF meters total is invalid.")
    elif valid_meter_values:
        actual_total = delivery.total_meters

        if actual_total != expected_total:
            add_error(
                "Meters total mismatch: "
                f"PDF = {expected_total:,}; "
                f"extracted = {actual_total:,}; "
                f"difference = {actual_total - expected_total:,}."
            )

    actual_packages = delivery.package_numbers
    expected_packages = delivery.expected_package_numbers
    expected_count = delivery.expected_package_count

    if expected_packages is None and expected_count is None:
        add_error(
            "No package count or package-number list "
            "was found for validation."
        )

    if expected_packages is not None:
        missing = expected_packages - actual_packages
        unexpected = actual_packages - expected_packages

        if missing:
            add_error(
                f"Missing package numbers: {sorted(missing)}."
            )

        if unexpected:
            add_error(
                f"Unexpected package numbers: {sorted(unexpected)}."
            )

        if (
            expected_count is not None
            and len(expected_packages) != expected_count
        ):
            add_error(
                "The PDF package-number list and "
                "declared package count disagree."
            )

    if (
        expected_count is not None
        and len(actual_packages) != expected_count
    ):
        add_error(
            "Package count mismatch: "
            f"PDF = {expected_count}; "
            f"extracted = {len(actual_packages)}."
        )

    return ValidationResult(
        delivery=delivery,
        errors=errors,
    )