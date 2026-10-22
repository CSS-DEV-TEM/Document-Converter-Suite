import argparse
from pathlib import Path

from app.batch_service import process_batch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and validate Pioneer packing-list PDFs."
    )

    parser.add_argument(
        "pdfs",
        nargs="*",
        help="One or more PDF file paths.",
    )

    args = parser.parse_args()

    project_dir = Path(__file__).resolve().parent

    if args.pdfs:
        paths = [Path(value) for value in args.pdfs]
    else:
        samples_dir = project_dir / "samples"

        paths = sorted(
            path
            for path in samples_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        ) if samples_dir.exists() else []

    batch = process_batch(paths)

    print()
    print("PIONEER DELIVERY NOTE CONVERTER")
    print("=" * 65)
    print(f"Selected files: {len(paths)}")

    for result in batch.results:
        delivery = result.delivery

        print()
        print(f"File: {delivery.source_path.name}")
        print("-" * 65)
        print(f"Invoice: {delivery.invoice}")
        print(f"LOT: {delivery.lot}")
        print(f"Packages: {len(delivery.package_numbers)}")
        print(f"Item rows: {len(delivery.rows)}")

        if all(row.meters.is_finite() for row in delivery.rows):
            print(f"Total meters: {delivery.total_meters:,}")

        print(f"Validation: {'PASS' if result.passed else 'FAIL'}")

        for error in result.errors:
            print(f"  ERROR: {error}")

        if result.passed:
            print()
            print("EXTRACTED ROWS")
            print("-" * 65)

            for row in delivery.rows:
                print(
                    f"{row.invoice} | "
                    f"{row.lot} | "
                    f"{row.package_no} | "
                    f"{row.carton_code} | "
                    f"{row.meters}"
                )

    if batch.batch_errors:
        print()
        print("BATCH ERRORS")
        print("-" * 65)

        for error in batch.batch_errors:
            print(f"  ERROR: {error}")

    print()
    print("BATCH SUMMARY")
    print("=" * 65)

    passed = sum(result.passed for result in batch.results)
    failed = sum(not result.passed for result in batch.results)

    print(f"Validated PDFs: {passed}")
    print(f"PDFs with validation failures: {failed}")
    print(f"Batch errors: {len(batch.batch_errors)}")

    if batch.can_export:
        print(f"Combined rows: {len(batch.validated_rows)}")
        print(f"Combined meters: {batch.total_meters:,}")
        print("EXTRACTION AND VALIDATION SUCCESSFUL")
    else:
        print("EXPORT BLOCKED: resolve the errors above.")

    print()
    print("Inspection only. No Excel file has been created.")

    return 0 if batch.can_export else 1


if __name__ == "__main__":
    raise SystemExit(main())