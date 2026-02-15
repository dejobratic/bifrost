from bifrost.core.errors import SshError
from bifrost.core.models import SetupConfig
from bifrost.infra.ssh import run_remote


def fetch_and_checkout(setup: SetupConfig, ref: str, latest: bool = False) -> None:
    if latest:
        result = run_remote(setup, ["git", "fetch", "--all"])
        if result.returncode != 0:
            raise SshError(f"git fetch failed on {setup.name}: {result.stderr.strip()}")

    result = run_remote(setup, ["git", "checkout", ref])
    if result.returncode != 0:
        raise SshError(f"git checkout '{ref}' failed on {setup.name}: {result.stderr.strip()}")

    if latest and _is_branch(ref):
        result = run_remote(setup, ["git", "pull", "--ff-only"])
        if result.returncode != 0:
            raise SshError(f"git pull failed on {setup.name}: {result.stderr.strip()}")


def _is_branch(ref: str) -> bool:
    return len(ref) != 40 or not all(c in "0123456789abcdef" for c in ref)
