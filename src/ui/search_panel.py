import os
from datetime import datetime
from typing import Set
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTextEdit, QPushButton,
                             QSlider, QRadioButton, QButtonGroup, QListWidget, QFileDialog, QCheckBox,
                             QListWidgetItem, QTextEdit as QLog, QProgressBar)
from PyQt5.QtCore import Qt, QUrl, QThread
from PyQt5.QtGui import QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

from ..db import DatabaseManager
from ..config import FILE_EXTS, DEFAULT_FUZZY_THRESHOLD
from ..search import fuzzy_search
from ..logger import logger
from ..threads.workers import IndexWorker

class SearchPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.selected_folder = None
        self.player = QMediaPlayer()
        self.index_thread: QThread = None
        self.index_worker: IndexWorker = None
        self._build_ui()
        self.player.positionChanged.connect(self._update_position)
        self.player.durationChanged.connect(self._update_duration)

    def _build_ui(self):
        main = QVBoxLayout(self)

        top = QHBoxLayout()
        self.input_text = QTextEdit(); top.addWidget(self.input_text)

        btns = QVBoxLayout()
        self.search_button = QPushButton("Buscar")
        self.folder_button = QPushButton("Elegir Carpeta")
        self.update_button = QPushButton("Actualizar Base de Datos (hilo)")
        self.clear_button = QPushButton("Limpiar")
        self.cancel_index_button = QPushButton("Cancelar Indexado")
        self.cancel_index_button.setEnabled(False)

        btns.addWidget(self.search_button)
        btns.addWidget(self.folder_button)
        btns.addWidget(self.update_button)
        btns.addWidget(self.cancel_index_button)
        btns.addWidget(self.clear_button)
        top.addLayout(btns)

        self.results = QListWidget(); top.addWidget(self.results)
        main.addLayout(top)

        # Controles de Reproducción
        controls = QHBoxLayout()
        self.play_pause_button = QPushButton("Play"); self.play_pause_button.setEnabled(False)
        self.progress_bar = QSlider(Qt.Horizontal); self.progress_bar.setRange(0, 100); self.progress_bar.setEnabled(False)
        controls.addWidget(self.play_pause_button); controls.addWidget(self.progress_bar)
        main.addLayout(controls)

        # Parámetros
        params = QGridLayout()
        params.addWidget(QLabel("Parámetros de Búsqueda:"), 0, 0, 1, 2)

        self.artist_radio = QRadioButton("Artista")
        self.song_radio = QRadioButton("Canción")
        self.song_radio.setChecked(True)
        group = QButtonGroup(); group.addButton(self.artist_radio); group.addButton(self.song_radio)
        params.addWidget(self.artist_radio, 1, 0); params.addWidget(self.song_radio, 1, 1)

        self.quality_slider = QSlider(Qt.Horizontal); self.quality_slider.setRange(0, 100); self.quality_slider.setValue(DEFAULT_FUZZY_THRESHOLD)
        self.intensity_label = QLabel(f"Intensidad de Búsqueda: {DEFAULT_FUZZY_THRESHOLD}%")
        self.quality_slider.valueChanged.connect(lambda v: self.intensity_label.setText(f"Intensidad de Búsqueda: {v}%"))
        params.addWidget(self.intensity_label, 2, 0); params.addWidget(self.quality_slider, 2, 1)

        params.addWidget(QLabel("Formatos de Archivo:"), 3, 0, 1, 2)
        ft = QGridLayout(); self.file_type_checkboxes = {}
        exts = sorted(list(FILE_EXTS)); r=c=0
        for e in exts:
            cb = QCheckBox(e.upper()); cb.setChecked(True); self.file_type_checkboxes[e]=cb
            ft.addWidget(cb, r, c); c+=1
            if c>3: c=0; r+=1
        params.addLayout(ft, 4, 0, 1, 2)
        main.addLayout(params)

        # Progreso + Log
        prog_row = QHBoxLayout()
        self.index_progress = QProgressBar(); self.index_progress.setRange(0, 100); self.index_progress.setValue(0)
        self.index_status = QLabel("Listo.")
        prog_row.addWidget(QLabel("Indexado:")); prog_row.addWidget(self.index_progress); prog_row.addWidget(self.index_status)
        main.addLayout(prog_row)

        self.log = QLog(); self.log.setReadOnly(True); self.log.setFixedHeight(90)
        main.addWidget(self.log)

        # conexiones
        self.folder_button.clicked.connect(self._select_folder)
        self.search_button.clicked.connect(self._perform_search)
        self.update_button.clicked.connect(self._update_database_threaded)
        self.cancel_index_button.clicked.connect(self._cancel_index)
        self.clear_button.clicked.connect(self._clear)
        self.results.itemDoubleClicked.connect(self._handle_double_click)
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        self.progress_bar.sliderMoved.connect(self.player.setPosition)

    def _allowed_exts(self) -> Set[str]:
        return {ext for ext, cb in self.file_type_checkboxes.items() if cb.isChecked()}

    # ---------- INDEXADO EN HILO ----------
    def _update_database_threaded(self):
        if not self.selected_folder:
            self._select_folder()
            if not self.selected_folder:
                self.log.append("No se seleccionó ninguna carpeta.")
                return
        # Preparar hilo + worker
        self.index_thread = QThread()
        self.index_worker = IndexWorker(self.selected_folder, self._allowed_exts())
        self.index_worker.moveToThread(self.index_thread)

        # Señales
        self.index_thread.started.connect(self.index_worker.run)
        self.index_worker.progress.connect(self._on_index_progress)
        self.index_worker.message.connect(self._on_index_message)
        self.index_worker.finished.connect(self._on_index_finished)
        self.index_worker.error.connect(self._on_index_error)

        # limpiar al finalizar
        self.index_worker.finished.connect(lambda _: self.index_thread.quit())
        self.index_worker.finished.connect(lambda _: self.index_worker.deleteLater())
        self.index_thread.finished.connect(lambda: self.index_thread.deleteLater())

        # UI estado
        self._toggle_index_ui(running=True)
        self.index_status.setText("Indexando...")

        self.index_thread.start()

    def _on_index_progress(self, current: int, total: int):
        pct = int((current / total) * 100) if total else 0
        self.index_progress.setValue(pct)

    def _on_index_message(self, msg: str):
        self.log.append(msg)

    def _on_index_finished(self, count: int):
        self.log.append(f"Indexado completado: {count} archivos añadidos.")
        self.index_status.setText("Completado.")
        self._toggle_index_ui(running=False)

    def _on_index_error(self, err: str):
        self.log.append(f"Error en indexado: {err}")
        self.index_status.setText("Error.")
        self._toggle_index_ui(running=False)

    def _cancel_index(self):
        if self.index_worker:
            self.index_worker.stop()
            self.log.append("Cancelando indexado...")

    def _toggle_index_ui(self, running: bool):
        self.update_button.setEnabled(not running)
        self.cancel_index_button.setEnabled(running)
        self.folder_button.setEnabled(not running)
        self.search_button.setEnabled(not running)
        self.clear_button.setEnabled(not running)

    # ---------- RESTO UI ----------
    def _select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if d:
            self.selected_folder = d
            self.log.append(f"Carpeta seleccionada: {d}")

    def _clear(self):
        self.input_text.clear(); self.results.clear(); self.log.clear()

    def _perform_search(self):
        rows = [s.strip() for s in self.input_text.toPlainText().strip().splitlines() if s.strip()]
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
                    self._add_result(m["title"] or m["name"] or q, "found", m["path"])
                found_any = True
            else:
                self._add_result(q, "not_found")
        self.log.append("Búsqueda completada (coincidencias encontradas)." if found_any else "Sin coincidencias.")

    def _add_result(self, name, status, path=None):
        item = QListWidgetItem(name)
        if status == "found":
            item.setForeground(QColor("green"))
            item.setToolTip(path or "")
        else:
            item.setForeground(QColor("red"))
            item.setToolTip("No encontrado.")
        self.results.addItem(item)

    def _handle_double_click(self, item):
        color = item.foreground().color().name()
        if color == "#008000":  # verde
            self._play(item.toolTip())
        elif color == "#ff0000":  # rojo
            self._assign_location(item)

    def _assign_location(self, item):
        file_path, _ = QFileDialog.getOpenFileName(self, "Asignar archivo", self.selected_folder or "")
        if file_path:
            item.setForeground(QColor("green"))
            item.setToolTip(file_path)
            self.log.append(f"Ubicación asignada a '{item.text()}'.")
            self.db.update_song_location(item.text(), file_path)

    def _play(self, path):
        if not path or not os.path.exists(path):
            self.log.append("Archivo no disponible.")
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.normpath(path))))
        self.player.play(); self.play_pause_button.setEnabled(True)
        self.log.append(f"Reproduciendo: {path}")

    def _toggle_play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause(); self.play_pause_button.setText("Play")
        else:
            self.player.play(); self.play_pause_button.setText("Pause")

    def _update_position(self, pos=None):
        self.progress_bar.setValue(self.player.position())

    def _update_duration(self, duration):
        self.progress_bar.setRange(0, duration); self.progress_bar.setEnabled(True)
