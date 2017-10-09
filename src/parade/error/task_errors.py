from parade.error import ParadeError

TASK_NOT_FOUND = (200, 404, 'task [{task}] not found')
DUPLICATED_TASK_EXIST = (201, 500, 'multiple tasks with name [{task}]')


class TaskNotFoundError(ParadeError):
    (code, status, message) = TASK_NOT_FOUND


class DuplicatedTaskExistError(ParadeError):
    (code, status, message) = DUPLICATED_TASK_EXIST
