from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import math

import pymupdf


class PdfReadError(Exception):
    """The PDF could not be read reliably."""


@dataclass(frozen=True)
class PdfPage:
    number: int
    text: str


def detect_text_angle(page: pymupdf.Page) -> int:
    votes: Counter[int] = Counter()

    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text_length = sum(
                len(span["text"].strip())
                for span in line["spans"]
            )

            if not text_length:
                continue

            x, y = line["dir"]
            actual_angle = math.degrees(math.atan2(y, x))
            nearest_angle = round(actual_angle / 90) * 90

            # Do not silently treat skewed text as an upright table.
            if abs(actual_angle - nearest_angle) > 5:
                continue

            votes[nearest_angle] += text_length

    if not votes:
        raise PdfReadError(
            f"Page {page.number + 1}: no usable text direction found. "
            "The page may be scanned or have an unsupported orientation."
        )

    return votes.most_common(1)[0][0]


def iter_pdf_pages(path: Path) -> Iterator[PdfPage]:
    path = Path(path)

    if not path.is_file():
        raise PdfReadError(f"PDF file not found: {path}")

    try:
        source = pymupdf.open(path)
    except Exception as exc:
        raise PdfReadError(f"Cannot open PDF: {path.name}") from exc

    with source, pymupdf.open() as normalized:
        if not source.is_pdf:
            raise PdfReadError("The selected file is not a PDF.")

        if source.needs_pass:
            raise PdfReadError(
                "The PDF is password protected. "
                "Use an unlocked copy."
            )

        if source.page_count == 0:
            raise PdfReadError("The PDF has no pages.")

        for page in source:
            try:
                # Text coordinates refer to the underlying page content.
                # Normalize from that content, independently of /Rotate.
                page.set_rotation(0)

                if not page.get_text().strip():
                    raise PdfReadError(
                        f"Page {page.number + 1}: no readable text. "
                        "OCR is required for this page."
                    )

                angle = detect_text_angle(page)

                width = page.rect.width
                height = page.rect.height

                if abs(angle) % 180:
                    width, height = height, width

                target = normalized.new_page(
                    width=width,
                    height=height,
                )

                target.show_pdf_page(
                    target.rect,
                    source,
                    page.number,
                    rotate=angle,
                )

                text = target.get_text(sort=True)

                if not text.strip():
                    raise PdfReadError(
                        f"Page {page.number + 1}: "
                        "text extraction returned no content."
                    )

                result = PdfPage(
                    number=page.number + 1,
                    text=text,
                )

            except PdfReadError:
                raise
            except Exception as exc:
                raise PdfReadError(
                    f"Page {page.number + 1}: "
                    f"reading failed: {exc}"
                ) from exc

            yield result