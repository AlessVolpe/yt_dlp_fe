from enum import IntEnum


class ExitCode(IntEnum):
    """
    Normalized exit codes for subprocesses run by the app.

    Raw subprocess return codes are mapped to these members where
    possible (see `ProcessWorker.run`) so calling code can compare
    against named values instead of magic numbers.

    Attributes:
        SUCCESS (int): The subprocess completed without error (0).
        GENERAL_ERROR (int): The subprocess failed or its return code
            could not be determined (1).
        PROCESS_FAILED (int): Reserved value indicating the process
            itself failed to run (-1).
        CANCELED (int): Reserved value indicating the process was
            canceled (-2).
        MISSING_EXECUTABLE (int): Reserved value indicating that
            the one or more dependencies were not found (-3).
    """

    SUCCESS = 0
    GENERAL_ERROR = 1
    PROCESS_FAILED = -1
    CANCELED = -2
    MISSING_EXECUTABLE = -3
