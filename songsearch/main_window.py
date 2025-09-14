from PyQt5.QtWidgets import QMainWindow, QTabWidget

from .ui.search_panel import SearchPanel
from .ui.organizer_panel import OrganizerPanel
from .config import APP_NAME


class MainWindow(QMainWindow):
    """Main application window.

    The window hosts two tabs: one for searching the database and another for
    organizing files.  Each tab is backed by its respective widget.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 700)
        tabs = QTabWidget()
        tabs.addTab(SearchPanel(self), "Buscar")
        tabs.addTab(OrganizerPanel(self), "Organizar")
        self.setCentralWidget(tabs)
