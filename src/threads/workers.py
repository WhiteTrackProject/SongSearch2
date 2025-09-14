from typing import List, Set
import os
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

# Importes locales (se importan aquí para evitar problemas de import cruzado en UI)
from ..db import DatabaseManager
from ..organizer.plan import plan_moves

class IndexWorker(QObject):
    """Escanea una carpeta y añade entradas a la DB en segundo plano."""
    progress = pyqtSignal(int, int)          # current, total
    message = pyqtSignal(str)                # log/status
    finished = pyqtSignal(int)               # count indexed
    error = pyqtSignal(str)

    def __init__(self, root_dir: str, allowed_exts: Set[str]):
        super().__init__()
        self.root_dir = root_dir
        self.allowed_exts = allowed_exts
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            db = DatabaseManager()
            # 1) pre-contar archivos para progreso
            files = []
            for r, _, fs in os.walk(self.root_dir):
                for f in fs:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in self.allowed_exts:
                        files.append(os.path.join(r, f))
            total = len(files)
            count = 0
            self.message.emit(f"Encontrados {total} archivos candidatos.")

            # 2) indexar
            for i, p in enumerate(files, start=1):
                if self._stop:
                    self.message.emit("Indexado cancelado por el usuario.")
                    break
                try:
                    name, ext = os.path.splitext(os.path.basename(p))
                    size = os.path.getsize(p)
                    mdate = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")
                    db.add_song(name=name, artist=None, title=None, album=None, year=None, month=None, genre=None,
                                path=p, duration=None, file_format=ext.lower(), size=size, modified_date=mdate,
                                original_path=p)
                    count += 1
                except Exception as e:
                    self.message.emit(f"Error indexando: {p} -> {e}")
                # Progreso
                self.progress.emit(i, total)
            self.finished.emit(count)
        except Exception as e:
            self.error.emit(str(e))


class DryRunWorker(QObject):
    """Genera un plan de Dry-Run (organizer) en segundo plano."""
    progress = pyqtSignal(int, int)          # current, total
    message = pyqtSignal(str)
    finished = pyqtSignal(list)              # plan list
    error = pyqtSignal(str)

    def __init__(self, src_dir: str, dest_dir: str, file_exts: Set[str]):
        super().__init__()
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self.file_exts = file_exts
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            # 1) recolectar archivos
            files: List[str] = []
            for root, _, fs in os.walk(self.src_dir):
                for f in fs:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in self.file_exts:
                        files.append(os.path.join(root, f))
            total = len(files)
            self.message.emit(f"Dry-Run: {total} archivos a procesar.")

            # 2) dividir en bloques y planificar (para progresos periódicos)
            if total == 0:
                self.finished.emit([])
                return

            # plan_moves ya procesa una lista; para progreso,
            # haremos chunks manuales.
            chunk = max(1, total // 20)  # ~20 pasos de progreso
            plan = []
            for i in range(0, total, chunk):
                if self._stop:
                    self.message.emit("Dry-Run cancelado por el usuario.")
                    break
                sub = files[i:i+chunk]
                subplan = plan_moves(sub, self.dest_dir)
                plan.extend(subplan)
                self.progress.emit(min(i+len(sub), total), total)

            self.finished.emit(plan)
        except Exception as e:
            self.error.emit(str(e))
