import argparse
from pathlib import Path

from app.batch_service import process_batch
from app.excel_exporter import ExcelExportError, export_batch


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export validated Pioneer PDFs to one Excel file."
    )

    parser.add_argument(
        "pdfs",
        nargs="*",
        help="PDF paths. If omitted, use all PDFs in samples.",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Destination .xlsx file.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file.",
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

    output_path = (
        Path(args.output)
        if args.output
        else project_dir / "output" / "Pioneer-Combined.xlsx"
    )

    print()
    print("PIONEER EXCEL EXPORT")
    print("=" * 65)
    print(f"Selected PDFs: {len(paths)}")

    batch = process_batch(paths)

    for result in batch.results:
        delivery = result.delivery
        status = "PASS" if result.passed else "FAIL"

        print(
            f"{delivery.source_path.name} | "
            f"{delivery.invoice} | "
            f"{len(delivery.rows)} rows | "
            f"{status}"
        )

        for error in result.errors:
            print(f"  ERROR: {error}")

    for error in batch.batch_errors:
        print(f"ERROR: {error}")

    if not batch.can_export:
        print()
        print("EXPORT BLOCKED")
        print("Resolve the errors above and run again.")
        return 1

    try:
        saved_path = export_batch(
            batch,
            output_path,
            overwrite=args.overwrite,
        )
    except ExcelExportError as exc:
        print()
        print(f"EXPORT FAILED: {exc}")
        return 1

    print()
    print("EXCEL EXPORT SUCCESSFUL")
    print("-" * 65)
    print(f"Validated PDFs: {len(batch.results)}")
    print(f"Exported rows: {len(batch.validated_rows)}")
    print(f"Total meters: {batch.total_meters:,}")
    print(f"Saved file: {saved_path}")
    print("Filters: enabled")
    print("Header: blue")
    print("Data rows: white")
    print("Sheet protection: disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())