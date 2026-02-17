import subprocess

from bifrost.shared import SetupConfig, SshError


def run_remote(
    setup: SetupConfig, command: list[str], capture: bool = True
) -> subprocess.CompletedProcess[str]:
    ssh_target = f"{setup.user}@{setup.host}"
    remote_cmd = " ".join(command)
    try:
        return subprocess.run(
            ["ssh", "-o", "BatchMode=yes", ssh_target, remote_cmd],
            capture_output=capture,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired as e:
        raise SshError(f"SSH command timed out on {setup.name}") from e
    except OSError as e:
        raise SshError(f"Failed to execute SSH to {setup.name}: {e}") from e


def check_reachable(setup: SetupConfig, timeout: int = 5) -> bool:
    ssh_target = f"{setup.user}@{setup.host}"
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                f"ConnectTimeout={timeout}",
                ssh_target,
                "true",
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def open_interactive_session(setup: SetupConfig) -> int:
    ssh_target = f"{setup.user}@{setup.host}"
    result = subprocess.run(["ssh", ssh_target])
    return result.returncode
