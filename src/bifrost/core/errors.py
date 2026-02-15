import sys


class BifrostError(Exception):
    exit_code: int = 1

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CiBusyError(BifrostError):
    exit_code = 2


class ConfigError(BifrostError):
    exit_code = 3


class SshError(BifrostError):
    exit_code = 4


class RemoteCommandError(BifrostError):
    exit_code = 5

    def __init__(self, message: str, remote_exit_code: int = 1) -> None:
        self.remote_exit_code = remote_exit_code
        super().__init__(message)


class ArtifactCopyError(BifrostError):
    exit_code = 6
