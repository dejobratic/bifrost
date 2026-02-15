# bifrost (bf)

A small, opinionated CLI for running commands on remote test setups ---
safely, repeatably, and with minimal friction.

**bifrost** acts as a bridge between your local development environment
and remote setups (e.g. office labs, hardware benches, secured
networks). It checks whether CI is already using a setup, runs commands
remotely when safe, and brings logs and artifacts back automatically.

The short alias **`bf`** is provided for daily use.

---

## Why bifrost exists

In environments where:

- tests require physical hardware
- CI/CD pipelines run on shared setups
- developers work locally but cannot directly access internal resources
- remote execution involves SSH, manual git pulls, and copying logs back

...the workflow becomes repetitive and error-prone.

**bifrost** replaces that with one consistent flow:

> check CI → run remotely → store artifacts → copy back

---

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone the repo
git clone <repo-url> && cd bifrost

# Install (creates venv automatically)
uv sync

# Verify
uv run bf --help
```

After installation, `bf` is available inside the venv. To use it without `uv run`, activate the venv:

```bash
source .venv/bin/activate
bf --help
```

### System requirements

- **ssh** and **rsync** must be available on your PATH
- SSH access to remote setups must be configured via `~/.ssh/config` or ssh-agent

---

## Quick start

1. Create a `.bifrost.yml` in your project root (see [Configuration](#configuration))
2. Run a command on a remote setup:

```bash
bf run --setup office-a -- pytest -m smoke
```

3. Check results:

```bash
bf logs last
```

---

## Commands

### `bf run` --- remote execution

```bash
bf run --setup office-a -- <command args...>
```

The full workflow:

1. Validates config
2. Resolves setup (explicit `--setup` or default from config)
3. Checks CI gate (fails if pipeline is busy)
4. Checks out git ref on remote (if `--ref` provided)
5. Executes the command remotely via SSH
6. Stores run metadata on the remote
7. Copies artifacts back locally

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--setup` | `-s` | Target setup name |
| `--ref` | `-r` | Git ref (branch/tag/commit) to checkout on remote |
| `--latest` | `-l` | Fetch latest changes before running |
| `--force` | `-f` | Skip CI gate check |
| `--dry-run` | | Show what would happen without executing |

**Examples:**

```bash
# Run smoke tests on office-a with latest main
bf run --setup office-a --ref main --latest -- pytest -m smoke

# Use the setup's default runner command
bf run --setup office-a

# Force run even if CI is busy
bf run --setup office-a --force -- make test

# Preview without executing
bf run --setup office-a --dry-run -- pytest
```

Everything after `--` is passed through to the remote host exactly as provided.
bifrost does not interpret or modify the command.

If no command is given after `--`, the setup's configured `runner` is used as the default.

### `bf status` --- CI and reachability

```bash
bf status
bf status --setup office-a
```

Shows a table with each setup's SSH reachability and CI pipeline state.

### `bf setups` --- list configured setups

```bash
bf setups
```

Lists all setups from the config with host, user, default runner, and which one is the default.

### `bf logs` --- view run logs

```bash
bf logs last                  # most recent run
bf logs <run-id>              # specific run
bf logs last --setup office-b # last run on a specific setup
```

Displays run metadata (setup, command, ref, exit code, timestamp) and any collected artifacts.

### `bf ssh` --- interactive session

```bash
bf ssh --setup office-a
```

Opens a standard SSH session to the setup for manual debugging.

---

## Configuration

bifrost looks for config in this order:

1. `.bifrost.yml` or `.bifrost.yaml` in the current directory
2. `~/.config/bifrost/config.yml`

### Example

```yaml
version: 1

defaults:
  setup: office-a

gitlab:
  url: "https://gitlab.example.com"
  project_id: 12345
  token_env: "GITLAB_TOKEN"     # env var name, NOT the token

setups:
  office-a:
    host: "10.0.0.5"
    user: "ci"
    runner: "pytest"              # default command when none given
    artifacts:
      remote_dir: ".bifrost"     # relative to project root on remote
      local_dir: ".bifrost/office-a"

  office-b:
    host: "10.1.0.7"
    user: "ci"
    runner: "./run_tests.sh"
    artifacts:
      remote_dir: ".bifrost"
      local_dir: ".bifrost/office-b"
```

### Config reference

| Field | Required | Description |
|-------|----------|-------------|
| `version` | yes | Must be `1` |
| `defaults.setup` | no | Setup used when `--setup` is omitted |
| `gitlab.url` | no | GitLab instance URL (omit entire `gitlab` block to disable CI gate) |
| `gitlab.project_id` | yes* | GitLab project ID (*required if `gitlab` block exists) |
| `gitlab.token_env` | yes* | Name of the env var holding the GitLab API token |
| `setups.<name>.host` | yes | SSH hostname or IP |
| `setups.<name>.user` | yes | SSH username |
| `setups.<name>.runner` | no | Default command when no `-- <cmd>` is given |
| `setups.<name>.artifacts.remote_dir` | no | Remote artifact directory (default: `.bifrost`) |
| `setups.<name>.artifacts.local_dir` | no | Local artifact directory (default: `.bifrost/<setup-name>`) |

---

## Security

- **No secrets in config files.** Tokens are read from environment variables. The config only stores the env var name (e.g. `token_env: "GITLAB_TOKEN"`).
- **SSH auth** relies entirely on your system SSH agent and `~/.ssh/config`. bifrost only stores `host` and `user`.
- Token values are never printed in output or error messages.

---

## Run metadata

Each run produces a folder under `.bifrost/<setup>/<run-id>/` (both remote and local) containing:

- `run.json` --- setup, ref, command, exit code, timestamp, artifact paths
- `run.log` --- command output
- Any additional artifacts from the run

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | CI pipeline busy |
| 3 | Config error |
| 4 | SSH/connectivity error |
| 5 | Remote command failed |
| 6 | Artifact copy failed |

---

## Architecture

bifrost uses three layers with clean separation:

```
src/bifrost/
  cli/    → thin CLI commands (typer + rich)
  core/   → domain models, config, run orchestration, error types
  infra/  → SSH, rsync, GitLab API, git operations (subprocess-based)
```

- CLI handles argument parsing and output formatting only
- Core contains all business logic; the `Runner` accepts protocol-based dependencies via constructor injection
- Infra wraps external systems (SSH, rsync, GitLab API) behind protocols for testability

No DI container. No plugin system. Constructor injection only.

### CI gate

The CI gate is protocol-based (`CiGate`), currently supporting:

- `NoneCiGate` --- always allows runs (used when no `gitlab` config is present)
- `GitLabCiGate` --- checks GitLab for running/pending pipelines

Adding new providers (GitHub Actions, Jenkins, etc.) means implementing the `CiGate` protocol.

### Tech stack

- **typer** for CLI
- **rich** for terminal output
- **httpx** for GitLab API
- **PyYAML** for config
- **System SSH/rsync** via subprocess (no Paramiko)
- **pytest** for testing

---

## Development

```bash
# Install with dev dependencies
uv sync

# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v
```

---

## Name

**Bifr&#246;st** is the bridge between worlds in Norse mythology.

> local machine &#8596; remote setups &#8596; CI environments
