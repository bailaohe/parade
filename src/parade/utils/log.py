import logging

_formatter = logging.Formatter(
        '%(asctime)s program_name %(levelname)s [%(process)d] [%(filename)s:%(lineno)s]: %(message)s')

_handler = None

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

logger = logging.getLogger()
logger.addHandler(_console_handler)
logger.setLevel(logging.DEBUG)


def setup_logging(log_path):
    global _handler
    global logger
    if _handler:
        logger.removeHandler(_handler)

    logger.debug("Logging path set to {}".format(log_path))
    _handler = logging.handlers.TimedRotatingFileHandler(log_path)
    _handler.setFormatter(_formatter)

    logger = logging.getLogger()
    logger.addHandler(_handler)
    logger.setLevel(logging.DEBUG)

