import os

# Ensure that tests run without a display server
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from songsearch.app import MainWindow


def test_mainwindow_is_visible(qtbot):
    """MainWindow should be instantiable and visible."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible()
