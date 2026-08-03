import logging

from storybuilder.utils.logging_config import get_logger, set_library_log_levels


def test_set_library_log_levels_default() -> None:
    # Arrange: reset levels to NOTSET
    logging.getLogger("urllib3").setLevel(logging.NOTSET)
    logging.getLogger("requests").setLevel(logging.NOTSET)

    # Act
    set_library_log_levels()

    # Assert
    assert logging.getLogger("urllib3").level == logging.WARNING  # ruff: ignore[assert]
    assert logging.getLogger("requests").level == logging.WARNING  # ruff: ignore[assert]


def test_set_library_log_levels_custom() -> None:
    # Arrange
    test_levels = {
        "custom.lib.1": logging.ERROR,
        "custom.lib.2": logging.DEBUG,
    }

    # Act
    set_library_log_levels(test_levels)

    # Assert
    assert logging.getLogger("custom.lib.1").level == logging.ERROR  # ruff: ignore[assert]
    assert logging.getLogger("custom.lib.2").level == logging.DEBUG  # ruff: ignore[assert]


def test_get_logger_basic():
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_get_logger_with_level():
    logger = get_logger("test_logger_level", level=logging.DEBUG)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_level"
    assert logger.level == logging.DEBUG
