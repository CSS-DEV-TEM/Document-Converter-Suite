from pathlib import Path
from typing import Iterable

from app.models import BatchResult
from app.parser import calculate_file_hash, parse_delivery
from app.validator import validate_delivery


def process_batch(paths: Iterable[Path]) -> BatchResult:
    batch = BatchResult()

    seen_hashes: dict[str, Path] = {}
    seen_deliveries: dict[tuple[str, str], Path] = {}

    for selected_path in paths:
        path = Path(selected_path).resolve()

        try:
            if not path.is_file():
                batch.batch_errors.append(
                    f"{path.name}: file not found."
                )
                continue

            if path.suffix.lower() != ".pdf":
                batch.batch_errors.append(
                    f"{path.name}: only PDF files are supported."
                )
                continue

            file_hash = calculate_file_hash(path)

            if file_hash in seen_hashes:
                original = seen_hashes[file_hash]

                batch.batch_errors.append(
                    f"{path.name}: duplicate PDF content; "
                    f"already selected as {original.name}."
                )
                continue

            seen_hashes[file_hash] = path

            delivery = parse_delivery(path)

            if delivery.file_hash != file_hash:
                batch.batch_errors.append(
                    f"{path.name}: file changed during processing. "
                    "Select the file again."
                )
                continue

            result = validate_delivery(delivery)
            batch.results.append(result)

            if result.passed:
                key = (delivery.invoice, delivery.lot)

                if key in seen_deliveries:
                    original = seen_deliveries[key]

                    batch.batch_errors.append(
                        f"{path.name}: invoice {delivery.invoice}, "
                        f"LOT {delivery.lot} also appears in "
                        f"{original.name}. Review both files "
                        "before exporting."
                    )
                else:
                    seen_deliveries[key] = path

        except Exception as exc:
            batch.batch_errors.append(
                f"{path.name}: {type(exc).__name__}: {exc}"
            )

    if not batch.results and not batch.batch_errors:
        batch.batch_errors.append("No PDF files were selected.")

    return batch