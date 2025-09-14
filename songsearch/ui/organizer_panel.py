"""Placeholder organizer panel widget.

This simple widget will eventually allow users to organize their music
collection.  For now it only displays a message indicating that the feature is
under development.
"""

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class OrganizerPanel(QWidget):
    """Minimal organizer panel used in the main window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Organizador en desarrollo"))
