import pytest
from songsearch import __main__ as main_module


def test_main_missing_pyqt_exits_with_message(monkeypatch, capsys):
    """main() should exit gracefully when PyQt is unavailable."""
    monkeypatch.setattr(main_module, 'QApplication', None)
    main_module._IMPORT_ERROR = RuntimeError('boom')
    with pytest.raises(SystemExit) as excinfo:
        main_module.main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert 'PyQt5 is required to run the GUI' in captured.err


def test_main_qt_start_failure(monkeypatch, capsys):
    """main() should handle errors during Qt startup."""
    def fake_qapp(argv):  # pylint: disable=unused-argument
        raise RuntimeError('no display')

    monkeypatch.setattr(main_module, 'QApplication', fake_qapp)
    main_module._IMPORT_ERROR = None
    with pytest.raises(SystemExit) as excinfo:
        main_module.main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert 'Failed to start the GUI' in captured.err
