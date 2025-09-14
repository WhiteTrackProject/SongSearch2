from pathlib import Path

from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QAction, QMainWindow, QTabWidget

from .ui.search_panel import SearchPanel
from .ui.organizer_panel import OrganizerPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SongSearch")
        self.resize(1100, 700)

        self.tabs = QTabWidget()
        self.search_panel = SearchPanel(self)
        self.organizer_panel = OrganizerPanel(self)
        self.tabs.addTab(self.search_panel, "Buscar")
        self.tabs.addTab(self.organizer_panel, "Organizar")
        self.setCentralWidget(self.tabs)

        qss_path = Path(__file__).parent / "ui" / "styles.qss"
        file = QFile(str(qss_path))
        if file.open(QFile.ReadOnly):
            self.setStyleSheet(file.readAll().data().decode())
            file.close()

        self._build_menus()

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        org_menu = menubar.addMenu("Organizar")
        act_select = QAction("Seleccionar archivos", self)
        act_dest = QAction("Seleccionar destino", self)
        act_run = QAction("Organizar ahora", self)
        org_menu.addAction(act_select)
        org_menu.addAction(act_dest)
        org_menu.addAction(act_run)
        act_select.triggered.connect(self.organizer_panel.select_files)
        act_dest.triggered.connect(self.organizer_panel.select_destination)
        act_run.triggered.connect(self.organizer_panel.organize_files)
