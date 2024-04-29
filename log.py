import logging
import sys


def initLogger(name):
    class DebugLevelFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.DEBUG

    logger = logging.getLogger(name)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s:%(name)s:%(lineno)i %(message)s"))
    handler.addFilter(DebugLevelFilter())
    logger.addHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    return logger


def setDebugLevel(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
