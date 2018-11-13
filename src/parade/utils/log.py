import logging
import os

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

_parade_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_parade_formatter)


def _reset_logger(logger):
    logger.setLevel(logging.DEBUG)
    logger.handlers = [_console_handler]

parade_logger = logging.getLogger('Parade')
_reset_logger(parade_logger)


def logger(exec=None, flow=None, task=None):
    if not exec:
        _reset_logger(parade_logger)
        return parade_logger

    if task:
        parade_exec_logger = logging.getLogger('Parade.Task[{}/{}]'.format(flow, task))
        _reset_logger(parade_exec_logger)
        log_dir = os.path.join('executing', str(exec), 'tasks')
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, task))
    else:
        parade_exec_logger = logging.getLogger('Parade.Flow[{}]'.format(flow))
        _reset_logger(parade_exec_logger)
        log_dir = os.path.join('executing', str(exec))
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, flow))

    handler.setFormatter(_parade_formatter)
    parade_exec_logger.addHandler(handler)
    parade_exec_logger.propagate = False
    return parade_exec_logger
