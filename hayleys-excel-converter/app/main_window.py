import hashlib
import sys

from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import (
    Qt,
    QSettings,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QActionGroup, QFont
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.extractor import extract_pdf, display_number
from app.exporter import export_excel


# --------------------------------------------------------------------------
# Theme
# --------------------------------------------------------------------------
def build_theme(dark):
    if dark:
        c = {
            "background": "#0c111d",
            "sidebar": "#0a0f1a",
            "surface": "#111827",
            "card": "#141c2e",
            "text": "#e6ecf7",
            "muted": "#8b98b0",
            "border": "#222d44",
            "button": "#1a2438",
            "hover": "#243250",
            "alternate": "#121a2b",
            "header": "#18233a",
            "header_text": "#b9c8e4",
            "selection": "#1e3a6e",
            "nav_active": "#17254a",
            "disabled": "#161f31",
            "disabled_text": "#5d6b84",
            "scroll": "#33425f",
            "drop_bg": "#101a2e",
        }
    else:
        c = {
            "background": "#f4f6fb",
            "sidebar": "#ffffff",
            "surface": "#ffffff",
            "card": "#ffffff",
            "text": "#16203a",
            "muted": "#64748b",
            "border": "#e1e7f0",
            "button": "#ffffff",
            "hover": "#eef3fb",
            "alternate": "#f7f9fd",
            "header": "#eef2f9",
            "header_text": "#33476a",
            "selection": "#dbe7ff",
            "nav_active": "#e8f0ff",
            "disabled": "#eef1f6",
            "disabled_text": "#8a96a8",
            "scroll": "#c3cfe0",
            "drop_bg": "#f0f5ff",
        }

    accent = "#4f7cff"
    accent_hover = "#3d68e8"

    return f"""
    QWidget {{
        background: {c["background"]};
        color: {c["text"]};
        font-family: "Segoe UI";
        font-size: 13px;
    }}

    QLabel {{
        background: transparent;
    }}

    /* ---------- Sidebar ---------- */
    QFrame#Sidebar {{
        background: {c["sidebar"]};
        border-right: 1px solid {c["border"]};
    }}

    QFrame#Sidebar QLabel {{
        background: transparent;
    }}

    QLabel#Logo {{
        background: {accent};
        color: #ffffff;
        border-radius: 10px;
        font-size: 20px;
        font-weight: 800;
    }}

    QLabel#BrandName {{
        font-size: 15px;
        font-weight: 700;
    }}

    QLabel#SectionLabel {{
        color: {c["muted"]};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }}

    QPushButton#Nav {{
        background: transparent;
        border: none;
        border-radius: 9px;
        padding: 11px 14px;
        text-align: left;
        color: {c["muted"]};
        font-weight: 600;
    }}

    QPushButton#Nav:hover {{
        background: {c["hover"]};
        color: {c["text"]};
    }}

    QPushButton#Nav:checked {{
        background: {c["nav_active"]};
        color: {accent};
    }}

    QPushButton#Appearance {{
        background: {c["button"]};
        border: 1px solid {c["border"]};
        border-radius: 9px;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
    }}

    QPushButton#Appearance:hover {{
        background: {c["hover"]};
        border-color: {accent};
    }}

    QPushButton#Appearance::menu-indicator {{
        image: none;
    }}

    /* ---------- Text ---------- */
    QLabel#Title {{
        font-size: 24px;
        font-weight: 700;
    }}

    QLabel#Muted {{
        color: {c["muted"]};
    }}

    QLabel#PanelTitle {{
        font-size: 14px;
        font-weight: 700;
    }}

    QLabel#CardValue {{
        font-size: 28px;
        font-weight: 700;
    }}

    QLabel#DropTitle {{
        font-size: 20px;
        font-weight: 700;
    }}

    QLabel#DropIcon {{
        background: rgba(79, 124, 255, 0.15);
        color: {accent};
        border-radius: 36px;
        font-size: 34px;
    }}

    /* ---------- Cards and panels ---------- */
    QFrame#Card, QFrame#Panel {{
        background: {c["card"]};
        border: 1px solid {c["border"]};
        border-radius: 14px;
    }}

    QFrame#Card QLabel, QFrame#Panel QLabel {{
        background: transparent;
        border: none;
    }}

    QFrame#DropZone {{
        background: {c["drop_bg"]};
        border: 2px dashed {accent};
        border-radius: 18px;
    }}

    QFrame#DropZone QLabel {{
        background: transparent;
        border: none;
    }}

    QFrame#DropZone[hover="true"] {{
        background: rgba(79, 124, 255, 0.18);
    }}

    /* ---------- Buttons ---------- */
    QPushButton {{
        background: {c["button"]};
        border: 1px solid {c["border"]};
        border-radius: 9px;
        padding: 10px 18px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {c["hover"]};
        border-color: {accent};
    }}

    QPushButton#Primary {{
        background: {accent};
        border: 1px solid {accent};
        color: #ffffff;
    }}

    QPushButton#Primary:hover {{
        background: {accent_hover};
    }}

    QPushButton#Danger {{
        color: #ef4444;
    }}

    QPushButton:disabled,
    QPushButton#Primary:disabled {{
        background: {c["disabled"]};
        color: {c["disabled_text"]};
        border-color: {c["border"]};
    }}

    /* ---------- Menus ---------- */
    QMenu {{
        background: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 6px;
    }}

    QMenu::item {{
        padding: 9px 28px 9px 16px;
        border-radius: 6px;
    }}

    QMenu::item:selected {{
        background: {c["selection"]};
    }}

    /* ---------- Inputs ---------- */
    QLineEdit, QComboBox {{
        background: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 9px;
        padding: 8px 14px;
    }}

    QLineEdit:focus, QComboBox:focus {{
        border-color: {accent};
    }}

    QLineEdit:disabled, QComboBox:disabled {{
        background: {c["disabled"]};
        color: {c["disabled_text"]};
    }}

    QComboBox QAbstractItemView {{
        background: {c["surface"]};
        color: {c["text"]};
        selection-background-color: {accent};
        selection-color: #ffffff;
        border: 1px solid {c["border"]};
    }}

    /* ---------- Lists, tables ---------- */
    QListWidget, QTableWidget, QTextEdit {{
        background: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 12px;
        selection-background-color: {c["selection"]};
        selection-color: {c["text"]};
    }}

    QListWidget {{
        outline: none;
    }}

    QListWidget::item {{
        padding: 11px 10px;
        margin: 3px 4px;
        border-radius: 9px;
    }}

    QListWidget::item:hover {{
        background: {c["hover"]};
    }}

    QListWidget::item:selected,
    QTableWidget::item:selected {{
        background: {c["selection"]};
        color: {c["text"]};
    }}

    QTableWidget {{
        alternate-background-color: {c["alternate"]};
        gridline-color: transparent;
        outline: none;
    }}

    QTableWidget::item {{
        padding: 3px 8px;
        border: none;
    }}

    QHeaderView::section {{
        background: {c["header"]};
        color: {c["header_text"]};
        padding: 11px 8px;
        border: none;
        border-right: 1px solid {c["border"]};
        font-weight: 700;
        font-size: 12px;
    }}

    QTableCornerButton::section {{
        background: {c["header"]};
        border: none;
    }}

    QSplitter::handle {{
        background: transparent;
    }}

    QStatusBar {{
        color: {c["muted"]};
        background: {c["background"]};
    }}

    QToolTip {{
        background: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 6px;
    }}

    /* ---------- Scrollbars ---------- */
    QScrollBar:vertical {{
        background: transparent;
        width: 12px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical {{
        background: {c["scroll"]};
        min-height: 28px;
        border-radius: 4px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 12px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c["scroll"]};
        min-width: 28px;
        border-radius: 4px;
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}

    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}

    QPushButton#ThemeIcon {{
        background: {c["button"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 9px;
        padding: 0;
        font-family: "Segoe UI Symbol";
        font-size: 23px;
    }}

    QPushButton#ThemeIcon:hover {{
        background: {c["hover"]};
        border-color: {accent};
    }}

    QPushButton#ThemeIcon::menu-indicator {{
        image: none;
    }}
    """


# --------------------------------------------------------------------------
# Background worker (unchanged logic)
# --------------------------------------------------------------------------
class ExtractWorker(QThread):
    progress = Signal(str)
    completed = Signal(object)

    def __init__(self, paths, known_hashes, parent=None):
        super().__init__(parent)
        self.paths = list(paths)
        self.known_hashes = set(known_hashes)

    def run(self):
        outcomes = []

        for file_path in self.paths:
            path = Path(file_path)
            self.progress.emit(f"Reading {path.name}...")

            try:
                digest = hashlib.sha256()

                with path.open("rb") as stream:
                    for chunk in iter(
                        lambda: stream.read(1024 * 1024),
                        b"",
                    ):
                        digest.update(chunk)

                fingerprint = digest.hexdigest()

                if fingerprint in self.known_hashes:
                    outcomes.append(
                        ("duplicate", str(path), fingerprint, None)
                    )
                    continue

                result = extract_pdf(path)
                self.known_hashes.add(fingerprint)

                outcomes.append(
                    ("result", str(path), fingerprint, result)
                )

            except Exception as error:
                outcomes.append(
                    ("error", str(path), None, str(error))
                )

        self.completed.emit(outcomes)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setFrameShape(QFrame.Shape.NoFrame)

    table.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )
    table.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows
    )
    table.setSelectionMode(
        QAbstractItemView.SelectionMode.SingleSelection
    )
    table.setHorizontalScrollMode(
        QAbstractItemView.ScrollMode.ScrollPerPixel
    )
    table.setVerticalScrollMode(
        QAbstractItemView.ScrollMode.ScrollPerPixel
    )

    table.setWordWrap(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(40)

    header = table.horizontalHeader()
    header.setMinimumSectionSize(45)
    header.setStretchLastSection(False)
    header.setHighlightSections(False)
    header.setDefaultAlignment(
        Qt.AlignmentFlag.AlignLeft
        | Qt.AlignmentFlag.AlignVCenter
    )
    header.setSectionResizeMode(
        QHeaderView.ResizeMode.Interactive
    )

    return table


def add_table_row(table, values):
    row_index = table.rowCount()
    table.insertRow(row_index)

    for column, value in enumerate(values):
        text = str(value)
        item = QTableWidgetItem(text)
        item.setToolTip(text)
        table.setItem(row_index, column, item)


def make_panel():
    panel = QFrame()
    panel.setObjectName("Panel")
    return panel


class DropZone(QFrame):
    """Big friendly area shown before any PDF is imported."""

    browse_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setProperty("hover", False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("⬆")
        icon.setObjectName("DropIcon")
        icon.setFixedSize(72, 72)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Drag & drop your packing list PDFs here")
        title.setObjectName("DropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(
            "Data is extracted, validated, and ready to "
            "export as a GRN Excel file"
        )
        hint.setObjectName("Muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button = QPushButton("Browse PDFs")
        self.button.setObjectName("Primary")
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setFixedWidth(170)
        self.button.clicked.connect(self.browse_requested)

        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(6)
        layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)

    def set_hover(self, value):
        self.setProperty("hover", value)
        self.style().unpolish(self)
        self.style().polish(self)


# --------------------------------------------------------------------------
# Main window
# --------------------------------------------------------------------------
class MainWindow(QMainWindow):
    PAGES = [
        ("Data Preview", "☰", "Review every roll extracted from your PDFs"),
        ("Batch Validation", "✔", "Compare PDF subtotals with the values we read"),
        ("Errors", "⚠", "Everything that needs your attention"),
    ]

    def __init__(self):
        super().__init__()

        self.results = []
        self.file_errors = []
        self.file_entries = {}
        self.hashes = set()

        self.worker = None
        self.busy = False
        self.dark_mode = True

        self.settings = QSettings(
            "Kaveesha",
            "HayleysExcelConverter",
        )

        saved_theme = str(
            self.settings.value("appearance/theme", "Dark")
        )

        self.theme_mode = (
            saved_theme
            if saved_theme in ("System", "Light", "Dark")
            else "Dark"
        )

        self.setWindowTitle("Hayleys Excel Converter")
        self.resize(1480, 920)
        self.setMinimumSize(1100, 680)
        self.setAcceptDrops(True)

        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.build_sidebar())
        root_layout.addWidget(self.build_main_area(), 1)

        # Filters connect after every widget exists.
        self.search_input.textChanged.connect(self.apply_filters)
        self.status_filter.currentTextChanged.connect(
            self.apply_filters
        )

        self.configure_tables()
        self.apply_theme()
        self.switch_page(0)
        self.refresh_views()
        self.set_busy(False)

        self.theme_timer = QTimer(self)
        self.theme_timer.setInterval(2000)
        self.theme_timer.timeout.connect(self.check_system_theme)
        self.theme_timer.start()

        self.statusBar().showMessage("Ready · Add PDFs to begin")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(12)

        logo = QLabel("H")
        logo.setObjectName("Logo")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_box = QVBoxLayout()
        name_box.setSpacing(0)

        name = QLabel("Hayleys")
        name.setObjectName("BrandName")

        tagline = QLabel("Excel Converter")
        tagline.setObjectName("Muted")

        name_box.addWidget(name)
        name_box.addWidget(tagline)

        brand.addWidget(logo)
        brand.addLayout(name_box, 1)

        layout.addLayout(brand)
        layout.addSpacing(20)

        section = QLabel("WORKSPACE")
        section.setObjectName("SectionLabel")
        layout.addWidget(section)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []

        for index, (label, icon, _) in enumerate(self.PAGES):
            button = QPushButton(f"{icon}   {label}")
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(
                lambda checked=False, i=index:
                self.switch_page(i)
            )

            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addSpacing(18)

        files_label = QLabel("IMPORTED FILES")
        files_label.setObjectName("SectionLabel")
        layout.addWidget(files_label)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.file_list.itemSelectionChanged.connect(
            self.update_remove_button
        )
        layout.addWidget(self.file_list, 1)

        self.remove_button = QPushButton("Remove selected")
        self.remove_button.clicked.connect(self.remove_selected)
        layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear all")
        self.clear_button.setObjectName("Danger")
        self.clear_button.clicked.connect(self.clear_all)
        layout.addWidget(self.clear_button)

        # Create the theme control here.
        # build_main_area() places it in the header.
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeIcon")
        self.theme_button.setFixedSize(42, 42)
        self.theme_button.setAccessibleName("Choose appearance")
        self.theme_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        theme_menu = QMenu(self.theme_button)

        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions = {}

        for mode in ("Light", "Dark", "System"):
            action = theme_menu.addAction(mode)
            action.setCheckable(True)
            action.setChecked(mode == self.theme_mode)

            self.theme_group.addAction(action)
            self.theme_actions[mode] = action

            action.triggered.connect(
                lambda checked=False, selected=mode:
                self.change_theme(selected)
            )

        self.theme_button.setMenu(theme_menu)

        layout.addSpacing(8)

        footer = QLabel("Developed by Kaveesha")
        footer.setObjectName("Muted")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        return sidebar

    def build_main_area(self):
        area = QWidget()

        layout = QVBoxLayout(area)
        layout.setContentsMargins(28, 24, 28, 12)
        layout.setSpacing(18)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.page_title = QLabel("Data Preview")
        self.page_title.setObjectName("Title")

        self.page_subtitle = QLabel("")
        self.page_subtitle.setObjectName("Muted")

        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)

        header.addLayout(title_box, 1)

        self.add_button = QPushButton("+  Add PDFs")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.add_files)

        self.export_button = QPushButton("⤓  Export to Excel")
        self.export_button.setObjectName("Primary")
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.clicked.connect(self.export_data)

        header.addWidget(self.theme_button)
        header.addWidget(self.add_button)
        header.addWidget(self.export_button)

        layout.addLayout(header)

        # Summary cards
        cards = QHBoxLayout()
        cards.setSpacing(14)

        self.card_values = {}

        card_specs = [
            ("Files", "❏", "59, 130, 246"),
            ("Roll rows", "☰", "139, 92, 246"),
            ("Passed batches", "✔", "34, 197, 94"),
            ("Issues", "⚠", "245, 158, 11"),
        ]

        for name, icon, rgb in card_specs:
            card = QFrame()
            card.setObjectName("Card")

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(18, 14, 18, 14)
            card_layout.setSpacing(14)

            icon_label = QLabel(icon)
            icon_label.setFixedSize(46, 46)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(
                f"background: rgba({rgb}, 0.16);"
                f"color: rgb({rgb});"
                "border-radius: 12px;"
                "font-size: 20px;"
            )

            text_box = QVBoxLayout()
            text_box.setSpacing(0)

            label = QLabel(name)
            label.setObjectName("Muted")

            value = QLabel("0")
            value.setObjectName("CardValue")

            text_box.addWidget(label)
            text_box.addWidget(value)

            card_layout.addWidget(icon_label)
            card_layout.addLayout(text_box, 1)

            self.card_values[name] = value
            cards.addWidget(card)

        layout.addLayout(cards)

        # Empty state / workspace
        self.content_stack = QStackedWidget()

        self.drop_zone = DropZone()
        self.drop_zone.browse_requested.connect(self.add_files)
        self.content_stack.addWidget(self.drop_zone)

        self.content_stack.addWidget(self.build_workspace())

        layout.addWidget(self.content_stack, 1)

        return area

    def build_workspace(self):
        workspace = QWidget()

        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search PO, invoice, batch, item or file..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(42)

        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All statuses",
            "PASS",
            "FAIL",
        ])
        self.status_filter.setMinimumWidth(140)
        self.status_filter.setMinimumHeight(42)

        self.reset_filters_button = QPushButton("Reset")
        self.reset_filters_button.setMinimumHeight(42)
        self.reset_filters_button.clicked.connect(
            self.reset_filters
        )

        filter_bar.addWidget(self.search_input, 1)
        filter_bar.addWidget(self.status_filter)
        filter_bar.addWidget(self.reset_filters_button)

        layout.addLayout(filter_bar)

        self.pages = QStackedWidget()

        self.preview = make_table([
            "Status",
            "Purchase Order",
            "Qty",
            "Batch No",
            "Roll No",
            "Invoice No",
            "Item",
            "Unit",
            "Page",
            "Source file",
        ])

        self.validation = make_table([
            "Status",
            "Invoice",
            "Batch",
            "Unit",
            "PDF rolls",
            "Read rolls",
            "PDF subtotal",
            "Read subtotal",
            "Difference",
            "Page",
            "Source file",
        ])

        self.errors = QTextEdit()
        self.errors.setReadOnly(True)
        self.errors.setAcceptDrops(False)

        self.pages.addWidget(self.preview)
        self.pages.addWidget(self.validation)
        self.pages.addWidget(self.errors)

        layout.addWidget(self.pages, 1)

        self.visible_count_label = QLabel()
        self.visible_count_label.setObjectName("Muted")
        self.visible_count_label.setWordWrap(True)
        layout.addWidget(self.visible_count_label)

        self.quantity_label = QLabel(
            "Validated quantities: —"
        )
        self.quantity_label.setObjectName("Muted")
        self.quantity_label.setWordWrap(True)
        layout.addWidget(self.quantity_label)

        self.export_note = QLabel(
            "Export includes every row from PASS files, "
            "regardless of preview filters."
        )
        self.export_note.setObjectName("Muted")
        self.export_note.setWordWrap(True)
        layout.addWidget(self.export_note)

        return workspace

    def configure_tables(self):
        settings = [
            (
                self.preview,
                [75, 125, 80, 110, 70, 105, 120, 55, 55, 140],
                (1, 3, 5, 6, 9),
            ),
            (
                self.validation,
                [75, 105, 110, 55, 85, 90, 115, 115, 95, 55, 140],
                (1, 2, 6, 7, 10),
            ),
        ]

        for table, widths, stretch_columns in settings:
            header = table.horizontalHeader()
            header.setStretchLastSection(False)

            for column, width in enumerate(widths):
                header.setSectionResizeMode(
                    column,
                    QHeaderView.ResizeMode.Interactive,
                )
                table.setColumnWidth(column, width)

            for column in stretch_columns:
                header.setSectionResizeMode(
                    column,
                    QHeaderView.ResizeMode.Stretch,
                )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def switch_page(self, index):
        label, _, subtitle = self.PAGES[index]

        self.nav_buttons[index].setChecked(True)
        self.pages.setCurrentIndex(index)
        self.page_title.setText(label)
        self.page_subtitle.setText(subtitle)

        self.apply_filters()

    # ------------------------------------------------------------------
    # Drag and drop
    # ------------------------------------------------------------------
    @staticmethod
    def pdf_paths_from_mime(mime):
        if not mime.hasUrls():
            return []

        return [
            url.toLocalFile()
            for url in mime.urls()
            if url.isLocalFile()
            and url.toLocalFile().lower().endswith(".pdf")
        ]

    def dragEnterEvent(self, event):
        if not self.busy and self.pdf_paths_from_mime(
            event.mimeData()
        ):
            self.drop_zone.set_hover(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_zone.set_hover(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.drop_zone.set_hover(False)

        paths = self.pdf_paths_from_mime(event.mimeData())

        if paths and not self.busy:
            event.acceptProposedAction()
            self.start_processing(paths)
        else:
            event.ignore()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def validated_rows(self):
        return [
            row
            for _, result in self.results
            if result.passed
            for row in result.rows
        ]

    def set_busy(self, busy):
        self.busy = busy

        self.add_button.setEnabled(not busy)
        self.add_button.setText(
            "Processing..." if busy else "+  Add PDFs"
        )
        self.drop_zone.button.setEnabled(not busy)

        self.clear_button.setEnabled(
            not busy and bool(self.file_entries)
        )

        self.export_button.setEnabled(
            not busy and bool(self.validated_rows())
        )

        self.update_remove_button()

    def add_files(self):
        if self.busy:
            return

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Hayleys packing lists",
            "",
            "PDF files (*.pdf)",
        )

        if paths:
            self.start_processing(paths)

    def start_processing(self, paths):
        if self.busy or not paths:
            return

        self.set_busy(True)

        self.worker = ExtractWorker(paths, self.hashes, self)

        self.worker.progress.connect(self.statusBar().showMessage)
        self.worker.completed.connect(self.receive_results)
        self.worker.finished.connect(self.worker_finished)

        self.worker.start()

    def receive_results(self, outcomes):
        duplicates = []

        for kind, path, fingerprint, payload in outcomes:
            name = Path(path).name

            if kind == "duplicate":
                duplicates.append(name)
                continue

            entry_id = uuid4().hex

            if kind == "error":
                error_message = f"{name} | {payload}"
                self.file_errors.append(error_message)

                self.file_entries[entry_id] = {
                    "result": None,
                    "error": error_message,
                    "fingerprint": None,
                }

                item = QListWidgetItem(f"✖  ERROR  ·  {name}")

            else:
                self.hashes.add(fingerprint)

                result_entry = (path, payload)
                self.results.append(result_entry)

                self.file_entries[entry_id] = {
                    "result": result_entry,
                    "error": None,
                    "fingerprint": fingerprint,
                }

                mark = "✔" if payload.passed else "✖"
                status = "PASS" if payload.passed else "FAIL"

                item = QListWidgetItem(
                    f"{mark}  {status}  ·  {name}\n"
                    f"     {len(payload.rows)} rolls"
                )

            item.setData(Qt.ItemDataRole.UserRole, entry_id)
            item.setToolTip(path)

            self.file_list.addItem(item)

        self.refresh_views()
        self.update_remove_button()

        if duplicates:
            QMessageBox.information(
                self,
                "Duplicate PDFs skipped",
                "These PDFs are already imported:\n\n"
                + "\n".join(duplicates),
            )

    def worker_finished(self):
        worker = self.worker
        self.worker = None

        if worker is not None:
            worker.deleteLater()

        self.set_busy(False)

        self.statusBar().showMessage(
            "Processing finished · Review validation before export"
        )

    def refresh_views(self):
        self.preview.setRowCount(0)
        self.validation.setRowCount(0)

        errors = list(self.file_errors)
        total_rows = 0
        passed_batches = 0

        for path, result in self.results:
            total_rows += len(result.rows)
            errors.extend(result.errors)

            file_status = "PASS" if result.passed else "FAIL"

            for row in result.rows:
                add_table_row(
                    self.preview,
                    [
                        file_status,
                        row.purchase_order,
                        display_number(row.quantity),
                        row.batch,
                        row.vendor_roll,
                        row.invoice,
                        row.item,
                        row.unit,
                        row.page,
                        Path(path).name,
                    ],
                )

            for check in result.checks:
                passed_batches += int(check.passed)

                add_table_row(
                    self.validation,
                    [
                        "PASS" if check.passed else "FAIL",
                        check.invoice,
                        check.batch,
                        check.unit,
                        check.expected_count,
                        check.actual_count,
                        display_number(check.expected_quantity),
                        display_number(check.actual_quantity),
                        display_number(check.difference),
                        check.page,
                        check.source_file,
                    ],
                )

                if not check.passed:
                    errors.append(
                        f"{check.source_file} | "
                        f"Page {check.page} | "
                        f"Batch {check.batch} | "
                        f"Rolls {check.actual_count}/"
                        f"{check.expected_count} | "
                        f"Quantity difference "
                        f"{display_number(check.difference)} "
                        f"{check.unit}"
                    )

        if not self.file_entries:
            error_text = "Add PDFs to begin validation."
        elif errors:
            error_text = "\n\n".join(errors)
        else:
            error_text = "No errors detected."

        self.errors.setPlainText(error_text)

        self.card_values["Files"].setText(str(len(self.file_entries)))
        self.card_values["Roll rows"].setText(str(total_rows))
        self.card_values["Passed batches"].setText(str(passed_batches))
        self.card_values["Issues"].setText(str(len(errors)))

        # Sidebar counters
        counts = [total_rows, self.validation.rowCount(), len(errors)]

        for index, (label, icon, _) in enumerate(self.PAGES):
            suffix = f"    {counts[index]}" if counts[index] else ""
            self.nav_buttons[index].setText(f"{icon}   {label}{suffix}")

        totals = defaultdict(lambda: Decimal("0"))

        for row in self.validated_rows():
            totals[row.unit] += row.quantity

        quantity_text = "   |   ".join(
            f"{unit}: {display_number(quantity)}"
            for unit, quantity in sorted(totals.items())
        )

        self.quantity_label.setText(
            "Validated quantities: " + (quantity_text or "—")
        )

        # Empty state vs workspace
        self.content_stack.setCurrentIndex(
            1 if self.file_entries else 0
        )

        numeric_columns = (
            (self.preview, (2,)),
            (self.validation, (4, 5, 6, 7, 8)),
        )

        for table, columns in numeric_columns:
            for row_index in range(table.rowCount()):
                for column in columns:
                    item = table.item(row_index, column)

                    if item is not None:
                        item.setTextAlignment(
                            Qt.AlignmentFlag.AlignRight
                            | Qt.AlignmentFlag.AlignVCenter
                        )

        export_count = len(self.validated_rows())
        self.export_button.setText(
            f"Export to Excel ({export_count})"
        )

        self.update_status_colors()
        self.apply_filters()

    def apply_filters(self, *_):
        query = self.search_input.text().strip().casefold()
        selected_status = self.status_filter.currentText()

        table_settings = [
            (self.preview, (1, 3, 4, 5, 6, 9)),
            (self.validation, (1, 2, 10)),
        ]

        visible_counts = {}

        for table, search_columns in table_settings:
            visible = 0

            for row in range(table.rowCount()):
                status_item = table.item(row, 0)
                status = (
                    status_item.text()
                    if status_item is not None
                    else ""
                )

                status_matches = (
                    selected_status == "All statuses"
                    or status == selected_status
                )

                search_values = [
                    table.item(row, column).text().casefold()
                    for column in search_columns
                    if table.item(row, column) is not None
                ]

                text_matches = not query or any(
                    query in value for value in search_values
                )

                show_row = status_matches and text_matches

                table.setRowHidden(row, not show_row)
                visible += int(show_row)

            visible_counts[id(table)] = visible

        current_page = self.pages.currentIndex()

        if current_page == 0:
            self.visible_count_label.setText(
                f"Showing {visible_counts[id(self.preview)]} "
                f"of {self.preview.rowCount()} roll rows"
                "  ·  Status refers to the whole PDF file"
            )

        elif current_page == 1:
            self.visible_count_label.setText(
                f"Showing {visible_counts[id(self.validation)]} "
                f"of {self.validation.rowCount()} batch sections"
                "  ·  Status refers to each batch check"
            )

        else:
            self.visible_count_label.setText(
                "All error details are shown here. "
                "Filters apply to the tables."
            )

        filters_enabled = current_page != 2
        self.search_input.setEnabled(filters_enabled)
        self.status_filter.setEnabled(filters_enabled)
        self.reset_filters_button.setEnabled(filters_enabled)

    def reset_filters(self):
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.apply_filters()

    def update_remove_button(self):
        self.remove_button.setEnabled(
            not self.busy and bool(self.file_list.selectedItems())
        )

    def remove_selected(self):
        if self.busy:
            return

        selected_items = self.file_list.selectedItems()

        if not selected_items:
            return

        for item in selected_items:
            entry_id = item.data(Qt.ItemDataRole.UserRole)
            entry = self.file_entries.pop(entry_id, None)

            if entry is None:
                continue

            result_entry = entry["result"]

            if result_entry is not None:
                self.results = [
                    existing
                    for existing in self.results
                    if existing is not result_entry
                ]

            error_message = entry["error"]

            if (
                error_message is not None
                and error_message in self.file_errors
            ):
                self.file_errors.remove(error_message)

            self.file_list.takeItem(self.file_list.row(item))

        self.hashes = {
            entry["fingerprint"]
            for entry in self.file_entries.values()
            if entry["fingerprint"] is not None
        }

        self.refresh_views()
        self.set_busy(False)

        self.statusBar().showMessage(
            "Selected PDF removed · Totals and export data updated"
        )

    def clear_all(self):
        if self.busy:
            return

        self.results.clear()
        self.file_errors.clear()
        self.file_entries.clear()
        self.hashes.clear()
        self.file_list.clear()

        self.reset_filters()
        self.refresh_views()
        self.set_busy(False)

        self.statusBar().showMessage("Ready · Add PDFs to begin")

    def export_data(self):
        if self.busy:
            return

        rows = self.validated_rows()

        if not rows:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GRN Excel",
            "Hayleys-GRN.xlsx",
            "Excel workbook (*.xlsx)",
        )

        if not path:
            return

        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"

            if Path(path).exists():
                answer = QMessageBox.question(
                    self,
                    "Replace existing file?",
                    f"This file already exists:\n\n{path}\n\n"
                    "Do you want to replace it?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if answer != QMessageBox.StandardButton.Yes:
                    return

        try:
            export_excel(rows, path)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export failed",
                f"Could not save the Excel file.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Export complete",
            f"Exported {len(rows)} validated rows.\n\n{path}",
        )

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def system_uses_dark_theme(self):
        if sys.platform == "win32":
            try:
                import winreg

                registry_path = (
                    r"Software\Microsoft\Windows"
                    r"\CurrentVersion\Themes\Personalize"
                )

                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    registry_path,
                ) as key:
                    value, _ = winreg.QueryValueEx(
                        key,
                        "AppsUseLightTheme",
                    )

                return value == 0

            except OSError:
                pass

        hints = QApplication.instance().styleHints()

        if hasattr(hints, "colorScheme"):
            return hints.colorScheme() == Qt.ColorScheme.Dark

        return False

    def change_theme(self, theme):
        self.theme_mode = theme

        self.settings.setValue("appearance/theme", theme)

        self.theme_actions[theme].setChecked(True)
        self.apply_theme()

    def apply_theme(self):
        self.dark_mode = (
            self.system_uses_dark_theme()
            if self.theme_mode == "System"
            else self.theme_mode == "Dark"
        )

        QApplication.instance().setStyleSheet(
            build_theme(self.dark_mode)
        )

        symbols = {
            "Light": "☀",
            "Dark": "☾",
            "System": "◐",
        }

        self.theme_button.setText(
            symbols[self.theme_mode]
        )
        self.theme_button.setToolTip(
            f"Appearance: {self.theme_mode}"
        )

        self.update_status_colors()

    def update_status_colors(self):
        if self.dark_mode:
            pass_fg, fail_fg = QColor("#4ade80"), QColor("#fb7185")
            pass_bg = QColor(34, 197, 94, 40)
            fail_bg = QColor(244, 63, 94, 40)
        else:
            pass_fg, fail_fg = QColor("#15803d"), QColor("#b91c1c")
            pass_bg = QColor(34, 197, 94, 45)
            fail_bg = QColor(239, 68, 68, 40)

        bold = QFont()
        bold.setBold(True)

        for table in (self.preview, self.validation):
            for row in range(table.rowCount()):
                item = table.item(row, 0)

                if item is None:
                    continue

                passed = item.text() == "PASS"

                item.setForeground(pass_fg if passed else fail_fg)
                item.setBackground(pass_bg if passed else fail_bg)
                item.setFont(bold)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

    def check_system_theme(self):
        if self.theme_mode != "System":
            return

        if self.system_uses_dark_theme() != self.dark_mode:
            self.apply_theme()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_F
            and event.modifiers()
            & Qt.KeyboardModifier.ControlModifier
        ):
            if self.pages.currentIndex() == 2:
                self.switch_page(0)

            if self.content_stack.currentIndex() == 1:
                self.search_input.setFocus()
                self.search_input.selectAll()

            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.busy:
            QMessageBox.information(
                self,
                "Processing PDFs",
                "Please wait until PDF processing finishes.",
            )
            event.ignore()
            return

        self.settings.sync()
        event.accept()