from pathlib import Path
import os
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection

from app.models import BatchResult


class ExcelExportError(Exception):
    """The batch could not be exported safely."""


HEADERS = (
    "INVOICE",
    "LOT",
    "PACKAGE NO",
    "CARTON #",
    "MTS/BOX",
)


def export_batch(
    batch: BatchResult,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> Path:
    if not batch.can_export:
        raise ExcelExportError(
            "Export blocked. Resolve all PDF and batch errors first."
        )

    # Always use the complete batch, never the UI's filtered rows.
    rows = batch.validated_rows

    if not rows:
        raise ExcelExportError("There are no validated rows to export.")

    if len(rows) > 1_048_575:
        raise ExcelExportError(
            "The batch exceeds Excel's row limit for one worksheet."
        )

    output_path = Path(output_path).expanduser().resolve()

    if output_path.suffix.lower() != ".xlsx":
        raise ExcelExportError(
            "The output filename must end with .xlsx."
        )

    if output_path.exists() and not overwrite:
        raise ExcelExportError(
            f"The file already exists: {output_path.name}. "
            "Choose another filename or explicitly allow replacement."
        )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Pioneer Delivery Notes"

    workbook.properties.title = "Pioneer Delivery Note Converter"
    workbook.properties.subject = "Validated package details"

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="17365D",
    )

    white_fill = PatternFill(
        fill_type="solid",
        fgColor="FFFFFF",
    )

    header_font = Font(
        name="Calibri",
        size=11,
        bold=True,
        color="FFFFFF",
    )

    body_font = Font(
        name="Calibri",
        size=11,
        color="000000",
    )

    unlocked = Protection(locked=False)

    sheet.append(HEADERS)

    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )
        cell.protection = unlocked

    sheet.row_dimensions[1].height = 28

    for row_number, item in enumerate(rows, start=2):
        # Store identifiers as text and quantities as numbers.
        meters = (
            int(item.meters)
            if item.meters == item.meters.to_integral_value()
            else item.meters
        )

        sheet.append(
            [
                item.invoice,
                item.lot,
                item.package_no,
                item.carton_code,
                meters,
            ]
        )

        for cell in sheet[row_number]:
            cell.fill = white_fill
            cell.font = body_font
            cell.protection = unlocked
            cell.alignment = Alignment(
                horizontal="left",
                vertical="center",
            )

        # Explicit text values preserve identifier characters.
        # Setting data_type also prevents identifiers being formulas.
        for column in (1, 2, 4):
            cell = sheet.cell(row=row_number, column=column)
            cell.data_type = "s"
            cell.number_format = "@"

        package_cell = sheet.cell(row=row_number, column=3)
        package_cell.number_format = "0"
        package_cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        meters_cell = sheet.cell(row=row_number, column=5)

        decimal_places = max(
            0,
            -item.meters.normalize().as_tuple().exponent,
        )

        meters_cell.number_format = (
            "#,##0"
            if decimal_places == 0
            else "#,##0." + ("0" * decimal_places)
        )

        meters_cell.alignment = Alignment(
            horizontal="right",
            vertical="center",
        )

        sheet.row_dimensions[row_number].height = 21

    # Fit identifiers without making the worksheet excessively wide.
    invoice_width = max(len(row.invoice) for row in rows) + 4
    lot_width = max(len(row.lot) for row in rows) + 4
    carton_width = max(len(row.carton_code) for row in rows) + 4

    sheet.column_dimensions["A"].width = max(18, invoice_width)
    sheet.column_dimensions["B"].width = max(20, lot_width)
    sheet.column_dimensions["C"].width = 18
    sheet.column_dimensions["D"].width = max(22, carton_width)
    sheet.column_dimensions["E"].width = 18

    last_row = len(rows) + 1

    # Filter arrows on all five columns, with no initial filtering.
    sheet.auto_filter.ref = f"A1:E{last_row}"
    sheet.freeze_panes = "A2"

    sheet.sheet_view.showGridLines = False
    sheet.protection.sheet = False

    # Save to a temporary file first to avoid leaving a partial workbook.
    temporary_path: Path | None = None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            prefix=".pioneer-",
            suffix=".xlsx",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        workbook.save(temporary_path)
        workbook.close()

        if overwrite:
            os.replace(temporary_path, output_path)
        else:
            # Publish without replacing a file created in the meantime.
            try:
                os.link(temporary_path, output_path)
            except FileExistsError as exc:
                raise ExcelExportError(
                    "The output file already exists. "
                    "Choose another filename."
                ) from exc

        return output_path

    except PermissionError as exc:
        raise ExcelExportError(
            "Cannot save the Excel file. Close it if it is open "
            "in Excel and check the output folder permissions."
        ) from exc

    except OSError as exc:
        raise ExcelExportError(
            f"Could not save the Excel file: {exc}"
        ) from exc

    finally:
        workbook.close()

        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)