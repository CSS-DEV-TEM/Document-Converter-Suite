from pathlib import Path
from typing import Callable

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSettings,
    QSortFilterProxyModel,
    QThread,
    Qt,
    QUrl,
    Signal,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.batch_service import process_batch
from app.excel_exporter import export_batch
from app.models import BatchResult, ItemRow
from app.themes import build_stylesheet


HEADERS = (
    "INVOICE",
    "LOT",
    "PACKAGE NO",
    "CARTON #",
    "MTS/BOX",
)


class TaskThread(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, function: Callable, parent=None):
        super().__init__(parent)
        self.function = function

    def run(self):
        try:
            result = self.function()
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        else:
            self.succeeded.emit(result)


class DeliveryTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows: list[ItemRow] = []

    def set_rows(self, rows: list[ItemRow]):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = self.rows[index.row()]

        values = (
            row.invoice,
            row.lot,
            row.package_no,
            row.carton_code,
            row.meters,
        )

        value = values[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 4:
                return f"{value:,}"
            return str(value)

        if role == Qt.ItemDataRole.UserRole:
            if index.column() == 4:
                return float(value)
            return value

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() in (2, 4):
                return (
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )

            return (
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter
            )

        if role == Qt.ItemDataRole.ToolTipRole:
            return f"PDF source page: {row.source_page}"

        return None

    def headerData(
        self,
        section,
        orientation,
        role=Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return HEADERS[section]

        return str(section + 1)


class DeliveryWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings()
        self.paths: list[Path] = []
        self.batch: BatchResult | None = None
        self.task: TaskThread | None = None
        self.busy = False
        self.saved_path: Path | None = None

        self.setWindowTitle("Pioneer Delivery Note Converter")
        self.resize(1180, 780)
        self.setMinimumSize(820, 560)

        self.build_ui()

        saved_mode = str(
            self.settings.value("theme", "system")
        )

        self.theme_mode = (
            saved_mode
            if saved_mode in self.theme_buttons
            else "system"
        )

        self.theme_buttons[self.theme_mode].setChecked(True)
        self.apply_theme()

        QApplication.instance().styleHints().colorSchemeChanged.connect(
            self.system_theme_changed
        )

        self.update_controls()
        self.statusBar().showMessage(
            "Add Pioneer PDFs to start."
        )

    def build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(14)

        top = QHBoxLayout()

        title_area = QVBoxLayout()
        title_area.setSpacing(3)

        title = QLabel("Pioneer")
        title.setObjectName("Title")

        subtitle = QLabel("DELIVERY NOTE CONVERTER")
        subtitle.setObjectName("Muted")

        title_area.addWidget(title)
        title_area.addWidget(subtitle)
        top.addLayout(title_area)
        top.addStretch()

        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_buttons = {}

        for mode, symbol, tooltip in (
            ("light", "☀", "Light mode"),
            ("dark", "☾", "Dark mode"),
            ("system", "▣", "Use system theme"),
        ):
            button = QToolButton()
            button.setText(symbol)
            button.setCheckable(True)
            button.setFixedSize(40, 38)
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)

            button.clicked.connect(
                lambda checked=False, selected=mode:
                self.select_theme(selected)
            )

            self.theme_group.addButton(button)
            self.theme_buttons[mode] = button
            top.addWidget(button)

        layout.addLayout(top)

        self.metrics = QLabel(
            "0 PDFs selected  •  0 validated rows"
        )
        self.metrics.setObjectName("Metrics")
        self.metrics.setWordWrap(True)
        layout.addWidget(self.metrics)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        source_panel = QFrame()
        source_panel.setObjectName("Panel")

        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(14, 14, 14, 14)
        source_layout.setSpacing(10)

        source_title = QLabel("Source documents")
        source_title.setObjectName("Section")
        source_layout.addWidget(source_title)

        self.add_button = QPushButton("+ Add PDFs")
        self.add_button.clicked.connect(self.add_files)
        source_layout.addWidget(self.add_button)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.file_list.itemSelectionChanged.connect(
            self.update_controls
        )
        source_layout.addWidget(self.file_list, 1)

        remove_row = QHBoxLayout()

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_files)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_files)

        remove_row.addWidget(self.remove_button)
        remove_row.addWidget(self.clear_button)
        source_layout.addLayout(remove_row)

        self.process_button = QPushButton("Validate PDFs")
        self.process_button.setObjectName("Primary")
        self.process_button.clicked.connect(self.process_files)
        source_layout.addWidget(self.process_button)

        source_note = QLabel(
            "Select multiple files with Ctrl or Shift.\n"
            "All selected PDFs must pass before export."
        )
        source_note.setObjectName("Muted")
        source_note.setWordWrap(True)
        source_layout.addWidget(source_note)

        splitter.addWidget(source_panel)

        preview_panel = QFrame()
        preview_panel.setObjectName("Panel")

        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(10)

        preview_title = QLabel("Validated details")
        preview_title.setObjectName("Section")
        preview_layout.addWidget(preview_title)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.search_category = QComboBox()
        self.search_category.setMinimumWidth(155)
        self.search_category.setAccessibleName("Search category")
        self.search_category.setToolTip(
            "Choose the column you want to search"
        )

        # Data values match the table's zero-based column indexes.
        self.search_category.addItem("All columns", -1)
        self.search_category.addItem("Invoice", 0)
        self.search_category.addItem("LOT", 1)
        self.search_category.addItem("Package No", 2)
        self.search_category.addItem("Carton #", 3)
        self.search_category.addItem("Mts/Box", 4)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search all columns...")
        self.search.setClearButtonEnabled(True)

        self.search.textChanged.connect(self.filter_preview)
        self.search_category.currentIndexChanged.connect(
            self.change_search_category
        )

        search_row.addWidget(self.search_category)
        search_row.addWidget(self.search, 1)

        preview_layout.addLayout(search_row)

        self.model = DeliveryTableModel(self)

        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(
            -1,
            Qt.SortOrder.AscendingOrder,
        )
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setAlternatingRowColors(False)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().hide()

        preview_layout.addWidget(self.table, 1)

        self.preview_count = QLabel("Showing 0 of 0 rows")
        self.preview_count.setObjectName("Muted")
        preview_layout.addWidget(self.preview_count)

        export_note = QLabel(
            "Search filters the preview only. "
            "Excel includes all validated rows."
        )
        export_note.setObjectName("Muted")
        export_note.setWordWrap(True)
        preview_layout.addWidget(export_note)

        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 820])

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(
            "Validation results will appear here."
        )
        self.log.setMinimumHeight(65)
        self.log.setMaximumHeight(115)
        layout.addWidget(self.log)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        footer = QHBoxLayout()

        self.state_label = QLabel("Ready")
        self.state_label.setObjectName("Muted")
        footer.addWidget(self.state_label)
        footer.addStretch()

        self.open_button = QPushButton("Open Excel")
        self.open_button.clicked.connect(self.open_excel)
        footer.addWidget(self.open_button)

        self.export_button = QPushButton("Export Excel")
        self.export_button.setObjectName("Primary")
        self.export_button.clicked.connect(self.save_excel)
        footer.addWidget(self.export_button)

        layout.addLayout(footer)

    def select_theme(self, mode):
        self.theme_mode = mode
        self.settings.setValue("theme", mode)
        self.apply_theme()

    def system_theme_changed(self, scheme):
        if self.theme_mode == "system":
            self.apply_theme()

    def apply_theme(self):
        if self.theme_mode == "system":
            dark = (
                QApplication.instance().styleHints().colorScheme()
                == Qt.ColorScheme.Dark
            )
        else:
            dark = self.theme_mode == "dark"

        self.setStyleSheet(build_stylesheet(dark))

    def update_controls(self):
        has_files = bool(self.paths)

        self.add_button.setEnabled(not self.busy)
        self.clear_button.setEnabled(
            has_files and not self.busy
        )
        self.remove_button.setEnabled(
            bool(self.file_list.selectedItems())
            and not self.busy
        )
        self.process_button.setEnabled(
            has_files and not self.busy
        )

        self.export_button.setEnabled(
            not self.busy
            and self.batch is not None
            and self.batch.can_export
        )

        self.open_button.setEnabled(
            not self.busy
            and self.saved_path is not None
        )

    def invalidate_results(self):
        self.batch = None
        self.saved_path = None

        self.model.set_rows([])
        self.search.clear()
        self.log.clear()

        self.metrics.setText(
            f"{len(self.paths)} PDFs selected  •  0 validated rows"
        )
        self.state_label.setText("Ready to validate")

        self.update_preview_count()
        self.update_controls()

    def refresh_file_list(self):
        self.file_list.clear()

        for path in self.paths:
            item = QListWidgetItem(path.name)
            item.setToolTip(str(path))
            self.file_list.addItem(item)

    def add_files(self):
        start_dir = str(
            self.settings.value(
                "input_directory",
                str(Path.home()),
            )
        )

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Pioneer PDFs",
            start_dir,
            "PDF files (*.pdf)",
        )

        if not filenames:
            return

        added = False

        for filename in filenames:
            path = Path(filename).resolve()

            if path not in self.paths:
                self.paths.append(path)
                added = True

        self.settings.setValue(
            "input_directory",
            str(Path(filenames[0]).parent),
        )

        if added:
            self.refresh_file_list()
            self.invalidate_results()

    def remove_files(self):
        selected_rows = sorted(
            (
                self.file_list.row(item)
                for item in self.file_list.selectedItems()
            ),
            reverse=True,
        )

        for index in selected_rows:
            del self.paths[index]

        self.refresh_file_list()
        self.invalidate_results()

    def clear_files(self):
        self.paths.clear()
        self.refresh_file_list()
        self.invalidate_results()

    def start_task(self, function, success_handler, message):
        if self.busy:
            return

        self.busy = True
        self.state_label.setText(message)
        self.statusBar().showMessage(message)
        self.progress.setRange(0, 0)
        self.update_controls()

        self.task = TaskThread(function, self)
        self.task.succeeded.connect(success_handler)
        self.task.failed.connect(self.task_failed)
        self.task.finished.connect(self.task_finished)
        self.task.start()

    def task_finished(self):
        finished_task = self.task
        self.task = None
        self.busy = False

        self.progress.setRange(0, 1)
        self.progress.setValue(1)

        self.update_controls()

        if finished_task is not None:
            finished_task.deleteLater()

    def task_failed(self, message):
        self.log.appendPlainText(f"ERROR: {message}")
        self.state_label.setText("Operation failed")
        self.statusBar().showMessage(message)

        QMessageBox.critical(
            self,
            "Operation failed",
            message,
        )

    def process_files(self):
        selected_paths = tuple(self.paths)
        self.invalidate_results()

        self.start_task(
            lambda: process_batch(selected_paths),
            self.processing_complete,
            f"Validating {len(selected_paths)} PDF(s)...",
        )

    def processing_complete(self, batch):
        self.batch = batch
        self.model.set_rows(batch.validated_rows)

        messages = []

        for result in batch.results:
            delivery = result.delivery
            status = "PASS" if result.passed else "FAIL"

            messages.append(
                f"{status} | {delivery.source_path.name} | "
                f"{delivery.invoice} | "
                f"{len(delivery.rows)} rows"
            )

            for error in result.errors:
                messages.append(f"    {error}")

        for error in batch.batch_errors:
            messages.append(f"ERROR | {error}")

        self.log.setPlainText("\n".join(messages))

        passed = sum(
            result.passed for result in batch.results
        )

        self.metrics.setText(
            f"{passed}/{len(self.paths)} PDFs validated  •  "
            f"{len(batch.validated_rows):,} rows  •  "
            f"{batch.total_meters:,} meters"
        )

        if batch.can_export:
            message = "Validation complete. Ready to export."
        else:
            message = (
                "Export blocked. Review the errors, "
                "remove or correct the affected files, and validate again."
            )

        self.state_label.setText(
            "Ready to export"
            if batch.can_export
            else "Validation needs attention"
        )
        self.statusBar().showMessage(message)

        self.update_preview_count()
        self.update_controls()

    def change_search_category(self, index):
        category = self.search_category.currentText()

        if self.search_category.currentData() == -1:
            placeholder = "Search all columns..."
        else:
            placeholder = f"Search {category}..."

        self.search.setPlaceholderText(placeholder)
        self.filter_preview(self.search.text())

    def filter_preview(self, text):
        column = self.search_category.currentData()

        self.proxy.setFilterKeyColumn(
            -1 if column is None else int(column)
        )
        self.proxy.setFilterFixedString(text.strip())
        self.update_preview_count()

    def update_preview_count(self):
        self.preview_count.setText(
            f"Showing {self.proxy.rowCount():,} "
            f"of {self.model.rowCount():,} rows"
        )

    def save_excel(self):
        if self.batch is None or not self.batch.can_export:
            return

        export_dir = Path(
            str(
                self.settings.value(
                    "export_directory",
                    str(Path.home()),
                )
            )
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save combined Excel",
            str(export_dir / "Pioneer-Combined.xlsx"),
            "Excel workbook (*.xlsx)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )

        if not filename:
            return

        path = Path(filename)

        if path.suffix.lower() != ".xlsx":
            path = Path(str(path) + ".xlsx")

        overwrite = False

        if path.exists():
            answer = QMessageBox.question(
                self,
                "Replace existing file?",
                f"Replace {path.name}?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

            overwrite = True

        self.settings.setValue(
            "export_directory",
            str(path.parent),
        )

        # Capture the full validated batch.
        # The search proxy is never used for export.
        batch = self.batch

        self.start_task(
            lambda: export_batch(
                batch,
                path,
                overwrite=overwrite,
            ),
            self.export_complete,
            "Saving combined Excel...",
        )

    def export_complete(self, path):
        self.saved_path = Path(path)
        self.state_label.setText("Excel saved")
        self.statusBar().showMessage(
            f"Saved: {self.saved_path}"
        )
        self.log.appendPlainText(
            f"\nEXPORTED | {self.saved_path}"
        )
        self.update_controls()

    def open_excel(self):
        if self.saved_path is None:
            return

        if not self.saved_path.is_file():
            QMessageBox.warning(
                self,
                "File not found",
                "The exported file has been moved or deleted.",
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.saved_path))
        )

        if not opened:
            QMessageBox.warning(
                self,
                "Cannot open file",
                f"Open the file manually:\n{self.saved_path}",
            )

    def closeEvent(self, event):
        if self.busy:
            event.ignore()

            self.statusBar().showMessage(
                "Please wait for the current operation to finish "
                "before closing."
            )
            return

        event.accept()