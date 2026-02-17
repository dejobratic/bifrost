class BifrostError(Exception):
    exit_code: int = 1

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConfigError(BifrostError):
    exit_code = 3


class SshError(BifrostError):
    exit_code = 4


class LogCopyError(BifrostError):
    exit_code = 6
