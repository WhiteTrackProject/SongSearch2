from PyQt5.QtWidgets import QMainWindow, QTabWidget

from .ui.search_panel import SearchPanel
from .ui.organizer_panel import OrganizerPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SongSearch")
        self.resize(1100, 700)
        tabs = QTabWidget()
        tabs.addTab(SearchPanel(self), "Buscar")
        tabs.addTab(OrganizerPanel(self), "Organizar")
        self.setCentralWidget(tabs)

