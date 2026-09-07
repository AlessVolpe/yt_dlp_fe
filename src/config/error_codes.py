from enum import IntEnum

class ExitCode(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    PROCESS_FAILED = -1
    CANCELED = -2
    MISSING_EXECUTABLE = -3