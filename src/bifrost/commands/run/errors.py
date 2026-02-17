from bifrost.shared import BifrostError


class CiBusyError(BifrostError):
    exit_code = 2


class RemoteCommandError(BifrostError):
    exit_code = 5

    def __init__(self, message: str, remote_exit_code: int = 1) -> None:
        self.remote_exit_code = remote_exit_code
        super().__init__(message)
