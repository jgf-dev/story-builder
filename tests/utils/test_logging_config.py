import logging
from storybuilder.utils.logging_config import get_logger

def test_get_logger_basic():
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_get_logger_with_level():
    logger = get_logger("test_logger_level", level=logging.DEBUG)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_level"
    assert logger.level == logging.DEBUG
