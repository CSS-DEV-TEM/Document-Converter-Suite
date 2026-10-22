from decimal import Decimal
from pathlib import Path
import hashlib
import re

from app.models import ItemRow, ParsedDelivery
from app.pdf_reader import iter_pdf_pages


class PdfParseError(Exception):
    """The PDF does not match the supported Pioneer layout."""


INVOICE_RE = re.compile(r"\bME\d+\b")

LOT_RE = re.compile(
    r"LOT\s+NUMBER\s*:\s*(\S+)",
    re.IGNORECASE,
)

TABLE_HEADER_RE = re.compile(
    r"PACKAGE\s+NO\.",
    re.IGNORECASE,
)

PACKAGE_COUNT_RE = re.compile(
    r"\((\d+)\)\s*CARTONS\b",
    re.IGNORECASE,
)

PACKAGE_RANGE_RE = re.compile(
    r"C/NO\.\s*([\d,\- ]+)",
    re.IGNORECASE,
)

PACKAGE_START_RE = re.compile(
    r"^\s*(\d+)\s+LULU",
    re.IGNORECASE,
)

ITEM_RE = re.compile(
    r"\bLULU\S+",
    re.IGNORECASE,
)

CARTON_RE = re.compile(
    r"^\s*(\d{10})\b",
)

METERS_RE = re.compile(
    r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*M\b",
    re.IGNORECASE,
)

TOTAL_RE = re.compile(
    r"\bTOTAL\s*:",
    re.IGNORECASE,
)


def calculate_file_hash(path: Path) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def parse_package_numbers(text: str) -> set[int]:
    numbers: set[int] = set()

    for token in text.replace(" ", "").split(","):
        if not token:
            raise PdfParseError("The package-number list is incomplete.")

        if "-" in token:
            parts = token.split("-")

            if len(parts) != 2:
                raise PdfParseError(
                    f"Invalid package range: {token}"
                )

            start, end = map(int, parts)

            if start <= 0 or end < start or end - start > 100000:
                raise PdfParseError(
                    f"Invalid package range: {token}"
                )

            values = set(range(start, end + 1))
        else:
            value = int(token)

            if value <= 0:
                raise PdfParseError(
                    f"Invalid package number: {token}"
                )

            values = {value}

        if numbers.intersection(values):
            raise PdfParseError(
                f"Overlapping package numbers in the PDF: {token}"
            )

        numbers.update(values)

    return numbers


def read_meters(line: str, page_number: int) -> Decimal:
    match = METERS_RE.search(line)

    if not match:
        raise PdfParseError(
            f"Page {page_number}: meters value was not found "
            f"in this line: {line.strip()}"
        )

    return Decimal(match.group(1).replace(",", ""))


def parse_delivery(path: Path) -> ParsedDelivery:
    path = Path(path).resolve()

    delivery = ParsedDelivery(
        source_path=path,
        file_hash=calculate_file_hash(path),
        invoice="",
        lot="",
    )

    current_package: int | None = None

    # Package number, meters and the page where the item started.
    pending: tuple[int, Decimal, int] | None = None

    pages = iter_pdf_pages(path)

    try:
        for page in pages:
            table_header = TABLE_HEADER_RE.search(page.text)

            if not table_header:
                raise PdfParseError(
                    f"Page {page.number}: PACKAGE NO. heading "
                    "was not found."
                )

            header = page.text[:table_header.start()]
            body = page.text[table_header.end():]

            invoices = set(INVOICE_RE.findall(header))
            lots = set(LOT_RE.findall(header))

            if len(invoices) != 1:
                raise PdfParseError(
                    f"Page {page.number}: one ME-number invoice "
                    f"was expected; found {sorted(invoices)}."
                )

            if len(lots) != 1:
                raise PdfParseError(
                    f"Page {page.number}: one LOT number "
                    f"was expected; found {sorted(lots)}."
                )

            invoice = next(iter(invoices))
            lot = next(iter(lots))

            if not delivery.invoice:
                delivery.invoice = invoice
                delivery.lot = lot
            elif (
                invoice != delivery.invoice
                or lot != delivery.lot
            ):
                raise PdfParseError(
                    f"Page {page.number}: invoice or LOT changed "
                    "inside the package-detail section."
                )

            count_match = PACKAGE_COUNT_RE.search(header)

            if count_match:
                count = int(count_match.group(1))

                if (
                    delivery.expected_package_count is not None
                    and delivery.expected_package_count != count
                ):
                    raise PdfParseError(
                        "Conflicting package counts in the PDF."
                    )

                delivery.expected_package_count = count

            range_match = PACKAGE_RANGE_RE.search(header)

            if range_match:
                numbers = parse_package_numbers(
                    range_match.group(1).strip()
                )

                if (
                    delivery.expected_package_numbers is not None
                    and delivery.expected_package_numbers != numbers
                ):
                    raise PdfParseError(
                        "Conflicting package-number lists in the PDF."
                    )

                delivery.expected_package_numbers = numbers

            for line in body.splitlines():
                if TOTAL_RE.search(line):
                    if pending is not None:
                        raise PdfParseError(
                            "The final item is missing its carton code."
                        )

                    delivery.expected_meters = read_meters(
                        line,
                        page.number,
                    )

                    delivery.package_section_complete = True
                    break

                if ITEM_RE.search(line):
                    if pending is not None:
                        raise PdfParseError(
                            f"Page {page.number}: a new item started "
                            "before the previous carton code was found."
                        )

                    package_match = PACKAGE_START_RE.match(line)

                    if package_match:
                        current_package = int(
                            package_match.group(1)
                        )

                    if current_package is None:
                        raise PdfParseError(
                            f"Page {page.number}: item has no "
                            "associated package number."
                        )

                    pending = (
                        current_package,
                        read_meters(line, page.number),
                        page.number,
                    )

                    continue

                carton_match = CARTON_RE.match(line)

                if carton_match:
                    if pending is None:
                        raise PdfParseError(
                            f"Page {page.number}: carton code "
                            "has no associated item."
                        )

                    package_no, meters, source_page = pending

                    delivery.rows.append(
                        ItemRow(
                            invoice=delivery.invoice,
                            lot=delivery.lot,
                            package_no=package_no,
                            carton_code=carton_match.group(1),
                            meters=meters,
                            source_page=source_page,
                        )
                    )

                    pending = None

                elif METERS_RE.search(line):
                    # Prevent an unrecognized item format from
                    # disappearing silently.
                    raise PdfParseError(
                        f"Page {page.number}: unsupported quantity line: "
                        f"{line.strip()}"
                    )

            if delivery.package_section_complete:
                break

    finally:
        pages.close()

    if pending is not None:
        delivery.extraction_errors.append(
            "The last extracted item has no carton code."
        )

    return delivery