import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("Hayleys Excel Converter")
    application.setOrganizationName("Kaveesha")
    application.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()