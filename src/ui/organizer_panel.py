from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QProgressBar)
from PyQt5.QtCore import QThread
from typing import List
import os

from ..organizer.plan import export_plan_csv
from ..organizer.mb_client import detect_fpcalc
from ..config import FILE_EXTS
from ..threads.workers import DryRunWorker

class OrganizerPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.src_dir = None
        self.dest_dir = None
        self.plan = []
        self.thread: QThread = None
        self.worker: DryRunWorker = None

        layout = QVBoxLayout(self)

        ctrl = QHBoxLayout()
        self.src_btn = QPushButton("Elegir carpeta ORIGEN")
        self.dest_btn = QPushButton("Elegir carpeta DESTINO Base")
        self.run_btn = QPushButton("Previsualizar (Dry-Run en hilo)")
        self.cancel_btn = QPushButton("Cancelar Dry-Run"); self.cancel_btn.setEnabled(False)
        self.export_btn = QPushButton("Exportar CSV"); self.export_btn.setEnabled(False)
        ctrl.addWidget(self.src_btn); ctrl.addWidget(self.dest_btn)
        ctrl.addWidget(self.run_btn); ctrl.addWidget(self.cancel_btn); ctrl.addWidget(self.export_btn)
        layout.addLayout(ctrl)

        self.fpcalc_note = QLabel("")
        if detect_fpcalc():
            self.fpcalc_note.setText("✔ Huellas acústicas disponibles (fpcalc detectado).")
        else:
            self.fpcalc_note.setText("ℹ Instala 'fpcalc' (Chromaprint) para identificación avanzada.")
        layout.addWidget(self.fpcalc_note)

        self.dest_label = QLineEdit(); self.dest_label.setPlaceholderText("p.ej. D:/MusicOrganized")
        layout.addWidget(self.dest_label)

        # Progreso
        prog = QHBoxLayout()
        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0)
        self.status = QLabel("Listo.")
        prog.addWidget(QLabel("Dry-Run:")); prog.addWidget(self.progress); prog.addWidget(self.status)
        layout.addLayout(prog)

        # Tabla
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Estado","Motivo","Origen","Propuesto","Meta (Artista - Título)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # Conexiones
        self.src_btn.clicked.connect(self.select_src)
        self.dest_btn.clicked.connect(self.select_dest)
        self.run_btn.clicked.connect(self.run_dryrun_threaded)
        self.cancel_btn.clicked.connect(self.cancel_dryrun)
        self.export_btn.clicked.connect(self.export_csv)

    def select_src(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta ORIGEN")
        if d: self.src_dir = d

    def select_dest(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta DESTINO Base")
        if d:
            self.dest_dir = d
            self.dest_label.setText(d)

    # ---------- DRY-RUN EN HILO ----------
    def run_dryrun_threaded(self):
        self.dest_dir = self.dest_label.text().strip() or self.dest_dir
        if not self.src_dir or not self.dest_dir: 
            self.status.setText("Falta origen o destino.")
            return

        self.thread = QThread()
        self.worker = DryRunWorker(self.src_dir, self.dest_dir, FILE_EXTS)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.message.connect(self._on_message)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        self.worker.finished.connect(lambda _: self.thread.quit())
        self.worker.finished.connect(lambda _: self.worker.deleteLater())
        self.thread.finished.connect(lambda: self.thread.deleteLater())

        self._toggle_ui(running=True)
        self.status.setText("Calculando plan...")
        self.progress.setValue(0)
        self.table.setRowCount(0)

        self.thread.start()

    def _on_progress(self, current: int, total: int):
        pct = int((current / total) * 100) if total else 0
        self.progress.setValue(pct)

    def _on_message(self, msg: str):
        self.status.setText(msg)

    def _on_finished(self, plan: list):
        self.plan = plan
        self._render_table(plan)
        self.status.setText("Dry-Run completado.")
        self.progress.setValue(100)
        self.export_btn.setEnabled(bool(plan))
        self._toggle_ui(running=False)

    def _on_error(self, err: str):
        self.status.setText(f"Error: {err}")
        self._toggle_ui(running=False)

    def cancel_dryrun(self):
        if self.worker:
            self.worker.stop()
            self.status.setText("Cancelando...")

    def _toggle_ui(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        self.src_btn.setEnabled(not running)
        self.dest_btn.setEnabled(not running)
        self.export_btn.setEnabled(not running and bool(self.plan))

    def _render_table(self, plan):
        self.table.setRowCount(0)
        for row in plan:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["status"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["reason"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["original_path"]))
            self.table.setItem(r, 3, QTableWidgetItem(row["proposed_path"]))
            meta = f'{row.get("artist","")}' + " - " + f'{row.get("title","")}'
            meta = meta.strip(" -")
            self.table.setItem(r, 4, QTableWidgetItem(meta))

    def export_csv(self):
        if not self.plan: return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar CSV", "dryrun_mapping.csv", "CSV (*.csv)")
        if path: export_plan_csv(self.plan, path)
