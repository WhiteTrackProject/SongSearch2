"""Panel de organización de archivos de música.

Este panel permite al usuario seleccionar archivos y moverlos a una carpeta de
 destino basada en los metadatos de cada canción.  Las rutas se calculan usando
 las utilidades del módulo :mod:`songsearch.organizer`.
"""

from __future__ import annotations

import os
import shutil
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QStyle,
)

from ..organizer.plan import plan_moves


class OrganizerPanel(QWidget):
    """Panel que permite organizar archivos en carpetas de destino."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.file_paths: List[str] = []
        self.dest_dir: str = ""
        self._build_ui()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(5, 5, 5, 5)
        main.setSpacing(5)

        style = self.style()
        file_btn = QPushButton("Seleccionar Archivos")
        file_btn.setIcon(style.standardIcon(QStyle.SP_DialogOpenButton))
        file_btn.clicked.connect(self.select_files)

        dest_layout = QHBoxLayout()
        dest_layout.setContentsMargins(0, 0, 0, 0)
        dest_layout.setSpacing(5)
        dest_layout.addWidget(QLabel("Destino:"))
        self.dest_edit = QLineEdit()
        self.dest_edit.setReadOnly(True)
        dest_layout.addWidget(self.dest_edit)
        dest_btn = QPushButton("Elegir Destino")
        dest_btn.setIcon(style.standardIcon(QStyle.SP_DirOpenIcon))
        dest_btn.clicked.connect(self.select_destination)
        dest_layout.addWidget(dest_btn)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        top_layout.addWidget(file_btn)
        top_layout.addLayout(dest_layout)
        main.addLayout(top_layout)

        splitter = QSplitter(Qt.Vertical)
        self.files_list = QListWidget()
        splitter.addWidget(self.files_list)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        splitter.addWidget(self.log)
        main.addWidget(splitter)

        organize_btn = QPushButton("Organizar")
        organize_btn.setIcon(style.standardIcon(QStyle.SP_DialogApplyButton))
        organize_btn.clicked.connect(self.organize_files)
        main.addWidget(organize_btn)

    # -------------------------------------------------------------- actions --
    def select_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos")
        if paths:
            self.file_paths = list(paths)
            self.files_list.clear()
            self.files_list.addItems(paths)
            self.log.append(f"{len(paths)} archivos seleccionados.")

    def select_destination(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino")
        if d:
            self.dest_dir = d
            self.dest_edit.setText(d)
            self.log.append(f"Carpeta destino: {d}")

    def organize_files(self) -> None:
        if not self.file_paths:
            self.log.append("No se han seleccionado archivos.")
            return
        if not self.dest_dir:
            self.log.append("Seleccione una carpeta de destino.")
            return

        plan = plan_moves(self.file_paths, self.dest_dir)
        for item in plan:
            src = item.get("original_path", "")
            dest = item.get("proposed_path", "")
            if item.get("status") == "ok" and src and dest:
                try:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.move(src, dest)
                    self.log.append(f"Movido: {src} -> {dest}")
                except Exception as exc:  # pragma: no cover - logging only
                    self.log.append(f"Error al mover {src}: {exc}")
            else:
                reason = item.get("reason", "desconocido")
                self.log.append(f"Error con {src}: {reason}")
