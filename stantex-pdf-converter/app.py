from __future__ import annotations
from PySide6.QtGui import QIcon, QPainter, QPen, QPixmap
import sys
from types import SimpleNamespace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QSettings,
    QSortFilterProxyModel,
    QThread,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QDesktopServices, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from extractor import ExtractionResult, extract_pdf
from excel_exporter import export_excel
from input_reader import extract_input


APP_VERSION = "1.2.0"

THEMES = {
    "Light": {
        "background": "#F3F6FB",
        "surface": "#FFFFFF",
        "input": "#FFFFFF",
        "text": "#172033",
        "muted": "#64748B",
        "border": "#DCE3EE",
        "header": "#EDF2F9",
        "alternate": "#F8FAFD",
        "hover": "#EAF0FA",
        "selection": "#DBEAFE",
        "accent_text": "#1D4ED8",
        "disabled": "#94A3B8",
        "disabled_bg": "#E8EDF5",
    },
    "Dark": {
        "background": "#0D1422",
        "surface": "#151F30",
        "input": "#101A2B",
        "text": "#E5EDF8",
        "muted": "#9CACBF",
        "border": "#2A374C",
        "header": "#1B283D",
        "alternate": "#182437",
        "hover": "#24344D",
        "selection": "#234572",
        "accent_text": "#8BB8FF",
        "disabled": "#687A94",
        "disabled_bg": "#202D41",
    },
}


def build_stylesheet(colors):
    return """
    QWidget {
        font-family: "Segoe UI";
        font-size: 13px;
        color: %(text)s;
    }
    QMainWindow, QWidget#Root {
        background: %(background)s;
    }
    QLabel {
        background: transparent;
        border: none;
    }
    QLabel#Brand {
        color: %(accent_text)s;
        font-size: 12px;
        font-weight: 700;
    }
    QLabel#Title {
        font-size: 25px;
        font-weight: 700;
    }
    QLabel#SectionTitle {
        font-size: 15px;
        font-weight: 600;
    }
    QLabel#Muted {
        color: %(muted)s;
    }
    QLabel#Metric {
        font-size: 25px;
        font-weight: 700;
    }
    QFrame#Panel, QFrame#Card {
        background: %(surface)s;
        border: 1px solid %(border)s;
        border-radius: 10px;
    }
    QFrame#ActionBar {
        background: %(surface)s;
        border: 1px solid %(border)s;
        border-radius: 10px;
    }
    QPushButton {
        background: %(surface)s;
        border: 1px solid %(border)s;
        border-radius: 7px;
        padding: 10px 18px;
        font-weight: 600;
        min-height: 18px;
    }
    QPushButton:hover {
        background: %(hover)s;
    }
    QPushButton:focus {
        border: 1px solid #3B82F6;
    }
    QPushButton#Primary {
        background: #2563EB;
        color: #FFFFFF;
        border: 1px solid #2563EB;
    }
    QPushButton#Primary:hover {
        background: #1D4ED8;
    }
    QPushButton#ThemeButton {
        padding: 0px;
        min-height: 0px;
        border-radius: 7px;
    }
    QPushButton#ThemeButton:checked {
        background: %(selection)s;
        border: 1px solid #3B82F6;
    }
    QPushButton:disabled {
        color: %(disabled)s;
        background: %(disabled_bg)s;
        border: 1px solid %(border)s;
    }
    QLineEdit, QComboBox {
        background: %(input)s;
        border: 1px solid %(border)s;
        border-radius: 7px;
        padding: 9px 12px;
        min-height: 20px;
        selection-background-color: %(selection)s;
        selection-color: %(text)s;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #3B82F6;
    }
    QComboBox {
        min-width: 90px;
    }
    QComboBox QAbstractItemView {
        background: %(surface)s;
        color: %(text)s;
        border: 1px solid %(border)s;
        selection-background-color: %(selection)s;
        selection-color: %(text)s;
    }
    QTableView {
        background: %(surface)s;
        alternate-background-color: %(alternate)s;
        color: %(text)s;
        border: 1px solid %(border)s;
        border-radius: 6px;
        gridline-color: %(border)s;
        selection-background-color: %(selection)s;
        selection-color: %(text)s;
    }
    QHeaderView::section {
        background: %(header)s;
        color: %(text)s;
        padding: 10px 4px;
        border: none;
        border-bottom: 1px solid %(border)s;
        font-weight: 600;
    }
    QTableCornerButton::section {
        background: %(header)s;
        border: none;
    }
    QProgressBar {
        background: %(border)s;
        border: none;
        border-radius: 2px;
        min-height: 4px;
        max-height: 4px;
    }
    QProgressBar::chunk {
        background: #3B82F6;
        border-radius: 2px;
    }
    QToolTip {
        background: %(surface)s;
        color: %(text)s;
        border: 1px solid %(border)s;
        padding: 6px;
    }
    QListWidget {
        background: %(input)s;
        border: 1px solid %(border)s;
        border-radius: 7px;
        selection-background-color: %(selection)s;
        selection-color: %(text)s;
    }
    QListWidget::item { padding: 10px; }
    QMessageBox, QFileDialog, QDialog {
        background: %(surface)s;
    }
    """ % colors

def make_theme_icon(mode: str, color: str) -> QIcon:
    from math import cos, sin, pi

    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    if mode == "Light":
        painter.drawEllipse(8, 8, 8, 8)

        for step in range(8):
            angle = step * pi / 4
            painter.drawLine(
                round(12 + cos(angle) * 7),
                round(12 + sin(angle) * 7),
                round(12 + cos(angle) * 10),
                round(12 + sin(angle) * 10),
            )

    else:
        from PySide6.QtGui import QPainterPath

        moon = QPainterPath()
        moon.addEllipse(3, 3, 18, 18)

        cutout = QPainterPath()
        cutout.addEllipse(10, 0, 17, 17)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPath(moon.subtracted(cutout))

    painter.end()
    return QIcon(pixmap)

class RollTableModel(QAbstractTableModel):
    HEADINGS = [
        "Invoice",
        "Purchase order",
        "Item",
        "Color",
        "LOT",
        "Package",
        "Roll qty",
        "FOC",
        "N.W",
        "G.W",
    ]

    def __init__(self):
        super().__init__()
        self.rows = []
        self.accent_color = "#1D4ED8"

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()

    def set_accent(self, color):
        self.accent_color = color

        if self.rows:
            self.dataChanged.emit(
                self.index(0, 7),
                self.index(len(self.rows) - 1, 7),
                [Qt.ItemDataRole.ForegroundRole],
            )

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADINGS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        roll = self.rows[index.row()]

        values = [
            roll.invoice,
            roll.purchase_order,
            roll.item,
            roll.color,
            roll.lot,
            roll.package,
            format(roll.quantity, ",f"),
            roll.foc_note,
            (
                f"{roll.net_weight:,.2f}"
                if roll.net_weight is not None
                else ""
            ),
            (
                f"{roll.gross_weight:,.2f}"
                if roll.gross_weight is not None
                else ""
            ),
        ]

        if role == Qt.ItemDataRole.DisplayRole:
            return values[index.column()]

        if role == Qt.ItemDataRole.ToolTipRole:
            pages = ", ".join(map(str, roll.source_pages))
            return f"{values[index.column()]}\nPDF pages: {pages}" if pages else values[index.column()]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (6, 8, 9):
                return (
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.ForegroundRole:
            if index.column() == 7 and roll.foc_quantity:
                return QColor(self.accent_color)

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.HEADINGS[section]

            return str(section + 1)

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if (
                orientation == Qt.Orientation.Vertical
                or section in (6, 8, 9)
            ):
                return (
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )

            return (
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

        return None



def extract_multiple(paths):
    results = []
    reports = {}
    seen_invoices = {}
    for path in paths:
        try:
            result = extract_input(path)
            invoices = {row.invoice for row in result.rows}
            duplicates = invoices.intersection(seen_invoices)
            if duplicates:
                raise ValueError("Duplicate invoice(s): " + ", ".join(sorted(duplicates))
                                 + ". Keep only one source file per invoice.")
            for invoice in invoices:
                seen_invoices[invoice] = path.name
            results.append((path, result))
            detail = (f"{len(result.rows):,} rolls | {result.total_quantity:,f} YDS"
                      f" | N.W {result.total_net_weight:,.2f} | G.W {result.total_gross_weight:,.2f}")
            reports[str(path)] = ("Warning" if result.warnings else "Passed",
                                  detail + "\n" + ("\n".join(result.warnings) or "Printed totals matched."))
        except Exception as error:
            reports[str(path)] = ("Failed", str(error))

    combined = ExtractionResult(
        rows=[row for _, result in results for row in result.rows],
        page_count=sum(result.page_count for _, result in results),
        raw_row_count=sum(result.raw_row_count for _, result in results),
        checked_invoices=[invoice for _, result in results for invoice in result.checked_invoices],
        warnings=[f"{path.name}: {warning}" for path, result in results for warning in result.warnings]
                 + [f"{Path(path).name}: EXCLUDED — {detail}" for path, (status, detail)
                    in reports.items() if status == "Failed"],
    )
    return SimpleNamespace(result=combined, reports=reports, successful=len(results), total=len(paths))


class Worker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, action):
        super().__init__()
        self.action = action

    @Slot()
    def run(self):
        try:
            self.succeeded.emit(self.action())
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class FileSelectionDialog(QDialog):
    def __init__(self, paths, parent=None, reports=None):
        super().__init__(parent)
        self.setWindowTitle("Selected source documents")
        self.resize(760, 460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        hint = QLabel("Select files to remove. Apply changes to update the selection.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for path in paths:
            status, detail = (reports or {}).get(str(path), ("Not checked", str(path.parent)))
            description = f"[{status}] {path.name}"
            if status == "Failed":
                description += f"\n{detail}"
            item = QListWidgetItem(description)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(f"{path}\n{detail}" if status == "Failed" else str(path))
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)
        self.count_label = QLabel()
        layout.addWidget(self.count_label)
        actions = QHBoxLayout()
        self.remove_button = QPushButton("Remove selected")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_selected)
        actions.addWidget(self.remove_button)
        actions.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        apply = QPushButton("Apply changes")
        apply.setObjectName("Primary")
        apply.clicked.connect(self.accept)
        actions.addWidget(apply)
        layout.addLayout(actions)
        self.list_widget.itemSelectionChanged.connect(self.update_selection)
        self.update_selection()

    def update_selection(self):
        self.remove_button.setEnabled(bool(self.list_widget.selectedItems()))
        self.count_label.setText(f"{self.list_widget.count()} file(s) remaining")

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self.update_selection()

    def selected_paths(self):
        return [Path(self.list_widget.item(i).data(Qt.ItemDataRole.UserRole))
                for i in range(self.list_widget.count())]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "STANTEXConverter",
            "STANTEX PDF CONVERTER",
        )

        self.result: ExtractionResult | None = None
        self.pdf_paths: list[Path] = []
        self.last_export: Path | None = None
        self.thread = None
        self.worker = None
        self.busy = False
        self.file_reports = {}

        self.setWindowTitle("STANTEX PDF CONVERTER")
        self.resize(1360, 860)
        self.setMinimumSize(980, 680)

        self.build_ui()

        saved_theme = self.settings.value("theme", "Light")

        if saved_theme not in ("Light", "Dark"):
            saved_theme = (
                "Dark"
                if QApplication.instance().styleHints().colorScheme()
                == Qt.ColorScheme.Dark
                else "Light"
            )

        self.current_theme = saved_theme
        self.apply_theme()


    @staticmethod
    def label(text, object_name=None):
        widget = QLabel(text)
        if object_name:
            widget.setObjectName(object_name)
        return widget

    def build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()

        heading = QVBoxLayout()
        heading.setSpacing(5)
        heading.addWidget(self.label("STANTEX", "Brand"))
        heading.addWidget(self.label("PDF & Excel Converter", "Title"))
        heading.addWidget(
            self.label(
                "Packing-list extraction and Excel export",
                "Muted",
            )
        )
        header.addLayout(heading, 1)

        self.light_button = QPushButton()
        self.light_button.setObjectName("ThemeButton")
        self.light_button.setFixedSize(40, 40)
        self.light_button.setCheckable(True)
        self.light_button.setToolTip("Light mode")
        self.light_button.setAccessibleName("Light mode")
        self.light_button.clicked.connect(
            lambda: self.theme_changed("Light")
        )

        self.dark_button = QPushButton()
        self.dark_button.setObjectName("ThemeButton")
        self.dark_button.setFixedSize(40, 40)
        self.dark_button.setCheckable(True)
        self.dark_button.setToolTip("Dark mode")
        self.dark_button.setAccessibleName("Dark mode")
        self.dark_button.clicked.connect(
            lambda: self.theme_changed("Dark")
        )

        header.addWidget(self.light_button)
        header.addWidget(self.dark_button)

        layout.addLayout(header)

        # Source file
        source_panel = QFrame()
        source_panel.setObjectName("Panel")
        source_layout = QHBoxLayout(source_panel)
        source_layout.setContentsMargins(18, 16, 18, 16)
        source_layout.setSpacing(12)

        file_details = QVBoxLayout()
        file_details.setSpacing(5)
        file_details.addWidget(
            self.label("Source documents", "SectionTitle")
        )

        self.file_label = self.label(
            "Select STANTEX packing-list PDFs or Excel workbooks.",
            "Muted",
        )
        self.file_label.setWordWrap(True)
        file_details.addWidget(self.file_label)
        source_layout.addLayout(file_details, 1)

        self.choose_button = QPushButton("Add files")
        self.choose_button.clicked.connect(self.choose_pdf)
        source_layout.addWidget(self.choose_button)
        self.files_button = QPushButton("Files (0)")
        self.files_button.setEnabled(False)
        self.files_button.clicked.connect(self.manage_files)
        source_layout.addWidget(self.files_button)

        self.extract_button = QPushButton("Extract details")
        self.extract_button.setObjectName("Primary")
        self.extract_button.setEnabled(False)
        self.extract_button.clicked.connect(self.start_extraction)
        source_layout.addWidget(self.extract_button)

        layout.addWidget(source_panel)

        # Metrics
        cards = QHBoxLayout()
        cards.setSpacing(14)

        self.invoice_value = self.create_card(cards, "Vendor invoices")
        self.roll_value = self.create_card(cards, "Total rolls")
        self.quantity_value = self.create_card(
            cards, "Quantity / YDS"
        )
        self.foc_value = self.create_card(
            cards, "Packages with FOC"
        )

        layout.addLayout(cards)

        # Results
        results_panel = QFrame()
        results_panel.setObjectName("Panel")
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(16, 16, 16, 14)
        results_layout.setSpacing(12)

        results_toolbar = QHBoxLayout()
        results_toolbar.addWidget(
            self.label("Extracted details", "SectionTitle")
        )
        results_toolbar.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Search invoice, PO, item, color, LOT or package"
        )
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(330)
        self.search.setMaximumWidth(520)
        results_toolbar.addWidget(self.search, 1)

        results_layout.addLayout(results_toolbar)

        self.model = RollTableModel()

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setSelectionBehavior(
            QTableView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableView.EditTrigger.NoEditTriggers
        )
        self.table.setHorizontalScrollMode(
            QTableView.ScrollMode.ScrollPerPixel
        )
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().setMinimumWidth(44)

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setMinimumSectionSize(70)

        widths = [185, 150, 155, 310, 90, 95, 100, 90, 95, 95]
        for column, width in enumerate(widths):
            self.table.setColumnWidth(column, width)

        results_layout.addWidget(self.table, 1)

        self.row_label = self.label(
            "No data loaded. Select source files and extract their details.",
            "Muted",
        )
        self.row_label.setWordWrap(True)
        results_layout.addWidget(self.row_label)

        layout.addWidget(results_panel, 1)

        self.search.textChanged.connect(self.filter_rows)

        # Bottom actions
        action_bar = QFrame()
        action_bar.setObjectName("ActionBar")
        actions = QHBoxLayout(action_bar)
        actions.setContentsMargins(18, 14, 18, 14)
        actions.setSpacing(10)

        export_details = QVBoxLayout()
        export_details.setSpacing(4)
        export_details.addWidget(
            self.label("Excel output", "SectionTitle")
        )

        self.export_hint = self.label(
            "Template columns, filters and FOC notes included.",
            "Muted",
        )
        self.export_hint.setWordWrap(True)
        export_details.addWidget(self.export_hint)

        actions.addLayout(export_details, 1)

        self.open_button = QPushButton("Open Excel")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_export)
        actions.addWidget(self.open_button)

        self.export_button = QPushButton("Export all rows")
        self.export_button.setObjectName("Primary")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.start_export)
        actions.addWidget(self.export_button)

        layout.addWidget(action_bar)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.status = self.label(
            "Ready · Files are processed locally",
            "Muted",
        )
        self.status.setWordWrap(True)
        footer = QHBoxLayout()
        footer.addWidget(self.status, 1)
        credit = self.label(f"v{APP_VERSION} · Developed by Kaveesha", "Muted")
        credit.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.addWidget(credit)
        layout.addLayout(footer)

    def create_card(self, layout, title):
        card = QFrame()
        card.setObjectName("Card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 14, 20, 14)
        card_layout.setSpacing(7)

        card_layout.addWidget(self.label(title, "Muted"))

        value = self.label("—", "Metric")
        card_layout.addWidget(value)

        layout.addWidget(card, 1)
        return value

    @Slot(str)
    def theme_changed(self, theme):
        self.current_theme = theme
        self.settings.setValue("theme", theme)
        self.apply_theme()

    def apply_theme(self):
        app = QApplication.instance()
        colors = THEMES[self.current_theme] 

        palette = QPalette()
        roles = {
            QPalette.ColorRole.Window: colors["surface"],
            QPalette.ColorRole.WindowText: colors["text"],
            QPalette.ColorRole.Base: colors["input"],
            QPalette.ColorRole.AlternateBase: colors["alternate"],
            QPalette.ColorRole.Text: colors["text"],
            QPalette.ColorRole.Button: colors["surface"],
            QPalette.ColorRole.ButtonText: colors["text"],
            QPalette.ColorRole.Highlight: colors["selection"],
            QPalette.ColorRole.HighlightedText: colors["text"],
            QPalette.ColorRole.ToolTipBase: colors["surface"],
            QPalette.ColorRole.ToolTipText: colors["text"],
            QPalette.ColorRole.PlaceholderText: colors["muted"],
            QPalette.ColorRole.Link: colors["accent_text"],
        }

        for role, color in roles.items():
            palette.setColor(role, QColor(color))

        for role in (
            QPalette.ColorRole.Text,
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.ButtonText,
        ):
            palette.setColor(
                QPalette.ColorGroup.Disabled,
                role,
                QColor(colors["disabled"]),
            )

        app.setPalette(palette)
        app.setStyleSheet(build_stylesheet(colors))
        self.model.set_accent(colors["accent_text"])

        self.light_button.setIcon(
            make_theme_icon("Light", colors["text"])
        )
        self.dark_button.setIcon(
            make_theme_icon("Dark", colors["text"])
        )

        self.light_button.setChecked(self.current_theme == "Light")
        self.dark_button.setChecked(self.current_theme == "Dark")   

    def choose_pdf(self):
        initial_folder = (
            str(self.pdf_paths[0].parent)
            if self.pdf_paths else str(Path.home())
        )
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose STANTEX PDF or Excel files",
            initial_folder,
            "Supported files (*.pdf *.xlsx);;PDF files (*.pdf);;Excel workbooks (*.xlsx)",
        )
        if not filenames:
            return

        paths = list(dict.fromkeys(
            self.pdf_paths + [Path(name) for name in filenames]
        ))
        if paths != self.pdf_paths:
            self.pdf_paths = paths
            self.selection_changed()

    def manage_files(self):
        if self.busy:
            return
        dialog = FileSelectionDialog(self.pdf_paths, self, self.file_reports)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        paths = dialog.selected_paths()
        if paths != self.pdf_paths:
            self.pdf_paths = paths
            self.selection_changed()

    def selection_changed(self):
        names = [path.name for path in self.pdf_paths]
        self.file_label.setText(
            "Select STANTEX packing-list PDFs or Excel workbooks." if not names
            else names[0] if len(names) == 1
            else f"{len(names)} files selected - " + ", ".join(names[:2])
            + (" ..." if len(names) > 2 else "")
        )
        self.file_label.setToolTip("\n".join(map(str, self.pdf_paths)))
        self.files_button.setText(f"Files ({len(names)})")
        self.clear_results()
        self.set_controls()
        self.status.setText(
            f"{len(names)} file(s) selected. Click Extract details to refresh results."
            if names else "No files selected. Click Add files to begin."
        )

    def clear_results(self):
        self.file_reports = {}
        self.result = None
        self.last_export = None
        self.model.set_rows([])
        self.search.clear()

        for label in (
            self.invoice_value,
            self.roll_value,
            self.quantity_value,
            self.foc_value,
        ):
            label.setText("—")

        self.export_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.export_button.setText("Export all rows")
        self.row_label.setText("No extracted rows.")
        self.export_hint.setText(
            "Template columns, filters and FOC notes included."
        )
        self.progress.setValue(0)

    def start_extraction(self):
        if not self.pdf_paths or self.busy:
            return

        paths = list(self.pdf_paths)
        self.clear_results()

        self.run_task(
            lambda: extract_multiple(paths),
            self.extraction_done,
            f"Extracting {len(paths)} file(s) and checking totals...",
        )

    def run_task(self, action, success_handler, message):
        if self.busy:
            return

        self.busy = True
        self.set_controls()
        self.status.setText(message)
        self.progress.setRange(0, 0)

        self.thread = QThread(self)
        self.worker = Worker(action)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.succeeded.connect(success_handler)
        self.worker.failed.connect(self.task_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.task_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def set_controls(self):
        self.choose_button.setEnabled(not self.busy)
        self.files_button.setEnabled(not self.busy and bool(self.pdf_paths))
        self.extract_button.setEnabled(
            not self.busy and bool(self.pdf_paths)
        )
        self.export_button.setEnabled(
            not self.busy and self.result is not None
        )
        self.open_button.setEnabled(
            not self.busy and self.last_export is not None
        )

    @Slot(object)
    def extraction_done(self, batch):
        self.file_reports = batch.reports
        result = batch.result
        if not result.rows:
            self.status.setText("No files passed · Open Files for error details.")
            QMessageBox.critical(self, "No files could be extracted",
                                 "\n\n".join(result.warnings))
            return
        self.result = result
        self.model.set_rows(result.rows)
        invoices = list(dict.fromkeys(row.invoice for row in result.rows))
        self.invoice_value.setText(str(len(invoices)))
        self.invoice_value.setToolTip("\n".join(invoices))

        self.roll_value.setText(f"{len(result.rows):,}")
        self.quantity_value.setText(
            format(result.total_quantity, ",f")
        )
        self.foc_value.setText(
            str(sum(bool(row.foc_quantity) for row in result.rows))
        )

        self.export_button.setText(
            f"Export all {len(result.rows):,} rows"
        )
        self.export_hint.setText(
            f"Export includes {batch.successful} of {batch.total} source files · "
            "All extracted rows, regardless of search."
        )

        self.filter_rows(self.search.text())

        failures = [f"{Path(path).name}: {detail}"
                    for path, (status, detail) in batch.reports.items()
                    if status == "Failed"]
        self.status.setText(
            f"Extraction complete · {batch.successful} of {batch.total} files included"
            f" · {len(failures)} failed" if failures else
            f"Extraction complete · {batch.successful} file(s) · {len(result.rows):,} rows"
        )
        if failures:
            QMessageBox.warning(self, "Failed files", "\n\n".join(failures))

    @Slot(str)
    def filter_rows(self, text):
        self.proxy.setFilterFixedString(text.strip())

        if self.result:
            self.row_label.setText(
                f"Showing {self.proxy.rowCount():,} of "
                f"{len(self.result.rows):,} rows"
                " · Scroll horizontally for additional columns."
            )

    def start_export(self):
        if not self.result or self.busy:
            return

        default_name = (
            f"{self.pdf_paths[0].stem}-converted.xlsx"
            if len(self.pdf_paths) == 1
            else "STANTEX-combined.xlsx"
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel",
            str(Path.home() / default_name),
            "Excel workbook (*.xlsx)",
        )

        if not filename:
            return

        path = Path(filename)

        if path.suffix.lower() != ".xlsx":
            path = path.with_suffix(".xlsx")

            if path.exists():
                choice = QMessageBox.question(
                    self,
                    "Replace file?",
                    f"{path.name} already exists. Replace it?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if choice != QMessageBox.StandardButton.Yes:
                    return

        result = self.result
        self.run_task(
            lambda: export_excel(result, path),
            self.export_done,
            f"Exporting all {len(result.rows):,} rows...",
        )

    @Slot(object)
    def export_done(self, path):
        self.last_export = Path(path)
        self.status.setText(
            f"Excel saved successfully · {self.last_export}"
        )

    def open_export(self):
        if not self.last_export:
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.last_export))
        )

        if not opened:
            QMessageBox.warning(
                self,
                "Could not open Excel",
                f"Open the file manually:\n{self.last_export}",
            )

    @Slot(str)
    def task_failed(self, message):
        self.status.setText("Operation failed · See error details.")
        QMessageBox.critical(self, "STANTEX Converter", message)

    @Slot()
    def task_finished(self):
        self.busy = False
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.thread = None
        self.worker = None
        self.set_controls()

    def closeEvent(self, event):
        if self.busy:
            QMessageBox.information(
                self,
                "Processing",
                "Please wait for the current operation to finish "
                "before closing the application.",
            )
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("STANTEX PDF CONVERTER")
    app.setOrganizationName("STANTEXConverter")
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()