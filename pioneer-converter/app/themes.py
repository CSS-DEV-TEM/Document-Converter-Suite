def build_stylesheet(dark: bool) -> str:
    if dark:
        background = "#0B1220"
        surface = "#111D30"
        field = "#16243A"
        foreground = "#E8EFFA"
        muted = "#A3B3C9"
        border = "#2A3B54"
        selection = "#234A7A"
    else:
        background = "#F3F6FB"
        surface = "#FFFFFF"
        field = "#F8FAFD"
        foreground = "#172B46"
        muted = "#61748C"
        border = "#D9E2EE"
        selection = "#DCEAFF"

    return f"""
        QWidget {{
            font-family: "Segoe UI";
            font-size: 10pt;
            color: {foreground};
        }}

        QMainWindow, QWidget#Root {{
            background: {background};
        }}

        QFrame#Panel {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 14px;
        }}

        QLabel {{
            background: transparent;
            border: none;
        }}

        QLabel#Title {{
            font-size: 21pt;
            font-weight: 700;
        }}

        QLabel#Section {{
            font-size: 12pt;
            font-weight: 600;
        }}

        QLabel#Muted {{
            color: {muted};
        }}

        QLabel#Metrics {{
            font-size: 12pt;
            font-weight: 600;
            padding: 12px;
            background: {surface};
            border: 1px solid {border};
            border-radius: 10px;
        }}

        QPushButton, QToolButton {{
            background: {field};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 9px 14px;
            font-weight: 600;
        }}

        QPushButton:hover, QToolButton:hover {{
            border-color: #4689ED;
            background: {selection};
        }}

        QPushButton:disabled {{
            color: {muted};
            background: {background};
        }}

        QPushButton#Primary {{
            background: #2563EB;
            color: white;
            border: 1px solid #2563EB;
        }}

        QPushButton#Primary:hover {{
            background: #1D4ED8;
        }}

        QPushButton#Primary:disabled {{
            background: {field};
            color: {muted};
            border-color: {border};
        }}

        QToolButton {{
            font-size: 15pt;
            padding: 6px;
        }}

        QToolButton:checked {{
            background: #2563EB;
            color: white;
            border-color: #2563EB;
        }}

        QLineEdit {{
            background: {field};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 10px;
            selection-background-color: #2563EB;
            selection-color: white;
        }}

        QLineEdit:focus {{
            border-color: #4689ED;
        }}

        QListWidget, QTableView, QPlainTextEdit {{
            background: {surface};
            border: 1px solid {border};
            border-radius: 7px;
            selection-background-color: {selection};
            selection-color: {foreground};
        }}

        QListWidget::item {{
            padding: 10px 6px;
            border-bottom: 1px solid {border};
        }}

        QListWidget::item:selected {{
            background: {selection};
        }}

        QTableView::item {{
            padding: 5px;
        }}

        QHeaderView::section {{
            background: {field};
            color: {foreground};
            padding: 10px;
            border: none;
            border-bottom: 1px solid {border};
            font-weight: 600;
        }}

        QProgressBar {{
            background: {field};
            border: none;
            border-radius: 3px;
            max-height: 6px;
        }}

        QProgressBar::chunk {{
            background: #2563EB;
            border-radius: 3px;
        }}

        QSplitter::handle {{
            background: {background};
        }}

        QStatusBar {{
            background: {background};
            color: {muted};
        }}

        QToolTip {{
            background: {surface};
            color: {foreground};
            border: 1px solid {border};
            padding: 5px;
        }}

                QComboBox {{
            background: {field};
            color: {foreground};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 10px 12px;
            padding-right: 28px;
            min-height: 18px;
        }}

        QComboBox:hover, QComboBox:focus {{
            border-color: #4689ED;
        }}

        QComboBox::drop-down {{
            width: 24px;
            border: none;
        }}

        QComboBox QAbstractItemView {{
            background: {surface};
            color: {foreground};
            border: 1px solid {border};
            selection-background-color: {selection};
            selection-color: {foreground};
            outline: none;
        }}
    """