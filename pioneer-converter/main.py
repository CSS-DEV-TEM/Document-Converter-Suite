import sys

from PySide6.QtWidgets import QApplication
from app.ui import DeliveryWindow


def main() -> int:
    app = QApplication(sys.argv)

    app.setOrganizationName("PioneerTools")
    app.setApplicationName("PioneerDeliveryNoteConverter")
    app.setApplicationDisplayName(
        "Pioneer Delivery Note Converter"
    )

    app.setStyle("Fusion")

    window = DeliveryWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())