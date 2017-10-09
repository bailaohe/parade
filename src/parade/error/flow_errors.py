from . import ParadeError, FLOW_NOT_FOUND


class FlowNotFoundError(ParadeError):
    (code, status, message) = FLOW_NOT_FOUND
