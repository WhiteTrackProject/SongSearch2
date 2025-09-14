from songsearch import config


def test_config_has_app_name_and_mp3_extension():
    assert hasattr(config, "APP_NAME")
    assert ".mp3" in config.FILE_EXTS

