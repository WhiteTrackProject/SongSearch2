"""Graphical search panel for SongSearch.

This widget allows users to search and play songs from the database.  The
widget was originally written with a hard coded list of supported audio file
extensions for the checkboxes in the interface.  That meant that when the list
of supported formats in :mod:`songsearch.config` changed, the UI would not
reflect the new formats.

To keep the interface in sync with the configuration we now build the
checkboxes dynamically from ``FILE_EXTS``.  Any extension added to the
configuration will automatically appear in the UI.
"""

from __future__ import annotations

import os
from datetime import datetime

from mutagen import File

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QStyle,
    QSlider,
    QSplitter,
    QPlainTextEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config import DEFAULT_FUZZY_THRESHOLD, FILE_EXTS
from ..db import DatabaseManager
from ..logger import logger
from ..search import fuzzy_search


class SearchPanel(QWidget):
    """Widget that provides a search interface for the database."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db = DatabaseManager()
        self.selected_folder: str | None = None
        self.player = QMediaPlayer()
        self._build_ui()
        self.player.positionChanged.connect(self._update_position)
        self.player.durationChanged.connect(self._update_duration)

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        main = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("Introduce una canción o artista por línea")
        search_layout.addWidget(self.input_text)

        btns = QVBoxLayout()
        style = self.style()
        self.search_button = QPushButton("Buscar")
        self.search_button.setIcon(style.standardIcon(QStyle.SP_FileDialogContentsView))
        self.folder_button = QPushButton("Elegir Carpeta")
        self.folder_button.setIcon(style.standardIcon(QStyle.SP_DirOpenIcon))
        self.update_button = QPushButton("Actualizar Base de Datos")
        self.update_button.setIcon(style.standardIcon(QStyle.SP_BrowserReload))
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.setIcon(style.standardIcon(QStyle.SP_DialogResetButton))
        btns.addWidget(self.search_button)
        btns.addWidget(self.folder_button)
        btns.addWidget(self.update_button)
        btns.addWidget(self.clear_button)
        search_layout.addLayout(btns)
        main.addLayout(search_layout)

        splitter = QSplitter(Qt.Vertical)
        self.results = QListWidget()
        splitter.addWidget(self.results)

        controls_widget = QWidget()
        controls = QHBoxLayout(controls_widget)
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.setIcon(style.standardIcon(QStyle.SP_MediaPlay))
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setEnabled(False)
        controls.addWidget(self.play_pause_button)
        controls.addWidget(self.progress_bar)
        splitter.addWidget(controls_widget)

        main.addWidget(splitter)

        params = QGridLayout()
        self.artist_radio = QRadioButton("Artista")
        self.song_radio = QRadioButton("Canción")
        self.artist_radio.setChecked(False)
        self.song_radio.setChecked(True)
        group = QButtonGroup()
        group.addButton(self.artist_radio)
        group.addButton(self.song_radio)
        params.addWidget(self.artist_radio, 0, 0)
        params.addWidget(self.song_radio, 0, 1)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(0, 100)
        self.quality_slider.setValue(DEFAULT_FUZZY_THRESHOLD)
        self.intensity_label = QLabel(
            f"Intensidad de Búsqueda: {DEFAULT_FUZZY_THRESHOLD}%"
        )
        self.quality_slider.valueChanged.connect(
            lambda v: self.intensity_label.setText(f"Intensidad de Búsqueda: {v}%")
        )
        params.addWidget(self.intensity_label, 1, 0)
        params.addWidget(self.quality_slider, 1, 1)

        ft = QGridLayout()
        self.file_type_checkboxes: dict[str, QCheckBox] = {}

        # Build the checkboxes from the configured extensions instead of a
        # hard coded list so that new formats are automatically supported.
        r = c = 0
        for ext in sorted(FILE_EXTS):
            cb = QCheckBox(ext.upper())
            cb.setChecked(True)
            self.file_type_checkboxes[ext] = cb
            ft.addWidget(cb, r, c)
            c += 1
            if c > 3:
                c = 0
                r += 1
        file_formats_group = QGroupBox("Formatos de Archivo")
        file_formats_group.setLayout(ft)
        params.addWidget(file_formats_group, 2, 0, 1, 2)

        params_group = QGroupBox("Parámetros de búsqueda")
        params_group.setLayout(params)
        main.addWidget(params_group)

        # simple log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(70)
        main.addWidget(self.log)

        # connections
        self.folder_button.clicked.connect(self._select_folder)
        self.search_button.clicked.connect(self._perform_search)
        self.update_button.clicked.connect(self._update_database)
        self.clear_button.clicked.connect(self._clear)
        self.results.itemDoubleClicked.connect(self._handle_double_click)
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        self.progress_bar.sliderMoved.connect(self.player.setPosition)

    # ------------------------------------------------------------ interaction --
    def _select_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if d:
            self.selected_folder = d
            self.log.append(f"Carpeta seleccionada: {d}")

    def _update_database(self) -> None:
        if not self.selected_folder:
            self._select_folder()
            if not self.selected_folder:
                self.log.append("No se seleccionó ninguna carpeta.")
                return
        self.log.append("Actualizando la base de datos...")
        count = 0
        for root, _, files in os.walk(self.selected_folder):
            for f in files:
                name, ext = os.path.splitext(f)
                ext = ext.lower()
                if (
                    ext in FILE_EXTS
                    and self.file_type_checkboxes.get(ext, None)
                    and self.file_type_checkboxes[ext].isChecked()
                ):
                    p = os.path.join(root, f)
                    try:
                        audio = File(p, easy=True)
                        tags = audio.tags if audio else {}
                        artist = tags.get("artist", [None])[0] if tags else None
                        title = tags.get("title", [None])[0] if tags else None
                        album = tags.get("album", [None])[0] if tags else None
                        date = tags.get("date", [None])[0] if tags else None
                        year = month = None
                        if date:
                            if len(date) >= 4:
                                year = date[:4]
                            if len(date) >= 7:
                                month = date[5:7]
                        genre = tags.get("genre", [None])[0] if tags else None
                        duration = (
                            int(audio.info.length)
                            if audio is not None and getattr(audio, "info", None)
                            else None
                        )
                        size = os.path.getsize(p)
                        mdate = datetime.fromtimestamp(os.path.getmtime(p)).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        self.db.add_song(
                            name=name,
                            artist=artist,
                            title=title,
                            album=album,
                            year=year,
                            month=month,
                            genre=genre,
                            path=p,
                            duration=duration,
                            file_format=ext,
                            size=size,
                            modified_date=mdate,
                            original_path=p,
                        )
                        count += 1
                    except Exception as e:  # pragma: no cover - logging only
                        logger.error(f"Index error: {p} -> {e}")
        self.log.append(f"Base de datos actualizada con {count} archivos.")

    def _clear(self) -> None:
        self.input_text.clear()
        self.results.clear()
        self.log.clear()

    def _perform_search(self) -> None:
        rows = [s.strip() for s in self.input_text.toPlainText().splitlines() if s.strip()]
        if not rows:
            self.log.append("Introduce canciones o artistas.")
            return
        mode = "artist" if self.artist_radio.isChecked() else "song"
        thr = self.quality_slider.value()
        self.results.clear()
        found_any = False
        for q in rows:
            matches = fuzzy_search(self.db, q.lower(), mode, thr)
            if matches:
                for m in matches:
                    self._add_result(
                        m["title"] or m["name"] or q,
                        "found",
                        m["path"],
                        m["id"],
                    )
                found_any = True
            else:
                self._add_result(q, "not_found", identifier=q)
        if found_any:
            self.log.append("Búsqueda completada (coincidencias encontradas).")
        else:
            self.log.append("Sin coincidencias.")

    def _add_result(
        self,
        name: str,
        status: str,
        path: str | None = None,
        identifier: int | str | None = None,
    ) -> None:
        item = QListWidgetItem(name)
        item.setData(Qt.UserRole, status)
        if identifier is not None:
            item.setData(Qt.UserRole + 1, identifier)
        if status == "found":
            item.setForeground(QColor("green"))
            item.setToolTip(path or "")
        else:
            item.setForeground(QColor("red"))
            item.setToolTip("No encontrado.")
        self.results.addItem(item)

    def _handle_double_click(self, item: QListWidgetItem) -> None:
        status = item.data(Qt.UserRole)
        if status == "found":
            self._play(item.toolTip())
        elif status == "not_found":
            self._assign_location(item)

    def _assign_location(self, item: QListWidgetItem) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Asignar archivo", self.selected_folder or ""
        )
        if file_path:
            item.setForeground(QColor("green"))
            item.setToolTip(file_path)
            item.setData(Qt.UserRole, "found")
            self.log.append(f"Ubicación asignada a '{item.text()}'.")
            identifier = item.data(Qt.UserRole + 1) or item.text()
            self.db.update_song_location(identifier, file_path)

    def _play(self, path: str) -> None:
        if not path or not os.path.exists(path):
            self.log.append("Archivo no disponible.")
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.normpath(path))))
        self.player.play()
        self.play_pause_button.setEnabled(True)
        self.log.append(f"Reproduciendo: {path}")

    def _toggle_play_pause(self) -> None:
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_pause_button.setText("Play")
            self.play_pause_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )
        else:
            self.player.play()
            self.play_pause_button.setText("Pause")
            self.play_pause_button.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )

    def _update_position(self, pos: int | None = None) -> None:  # pragma: no cover
        # The ``pos`` parameter is part of the Qt signal but the method uses the
        # current player position for clarity.
        self.progress_bar.setValue(self.player.position())

    def _update_duration(self, duration: int) -> None:  # pragma: no cover
        self.progress_bar.setRange(0, duration)
        self.progress_bar.setEnabled(True)

