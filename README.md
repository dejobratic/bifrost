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

1. Add a setup configuration:

```bash
bf config add office-a --host 10.0.0.5 --user ci --runner pytest
bf config set-default office-a
```

2. (Optional) Add pipeline integration for CI checks:

```bash
bf pipeline add my-project --url https://gitlab.example.com --project-id 12345 --token-env GITLAB_TOKEN
```

3. Link the pipeline to your setup:

```bash
bf config add office-b --host 10.1.0.7 --user ci --pipeline my-project
```

4. Run a command on a remote setup:

```bash
bf run -- pytest -m smoke
```

5. Check logs in `.bifrost/office-a/<run-id>/`

---

## Commands

### `bf config` --- manage setup configurations

Non-interactive CLI commands for managing setups:

#### `bf config add`

```bash
bf config add <name> --host <host> --user <user> [OPTIONS]
```

Add a new setup configuration.

**Options:**
- `--host` (required): SSH hostname or IP
- `--user` (required): SSH username
- `--runner`: Default command to run (e.g., `pytest`)
- `--pipeline`: Reference to a pipeline configuration for CI checks
- `--remote-log-dir`: Remote log directory (default: `.bifrost/logs`)
- `--local-log-dir`: Local log directory (default: `.bifrost/<name>`)

**Examples:**
```bash
# Add a basic setup
bf config add office-a --host 10.0.0.5 --user ci --runner pytest

# Add a setup with pipeline integration
bf config add office-b --host 10.1.0.7 --user ci --pipeline my-project

# Set the default setup
bf config set-default office-a
```

#### `bf config list`

```bash
bf config list
```

Display all configured setups in a table.

#### `bf config edit`

```bash
bf config edit <name> [OPTIONS]
```

Edit an existing setup. Any option not provided will keep its current value.

**Example:**
```bash
bf config edit office-a --runner "pytest -v" --host 10.0.0.6
```

#### `bf config remove`

```bash
bf config remove <name>
```

Remove a setup configuration.

#### `bf config set-default`

```bash
bf config set-default <name>
```

Set the default setup to use when `--setup` is not specified.

### `bf pipeline` --- manage CI/CD pipeline integration

Manage named pipeline configurations for CI gate checks. Pipelines are referenced by setups to enable automatic CI busy checks before running commands.

#### `bf pipeline add`

```bash
bf pipeline add <name> --url <url> --project-id <id> --token-env <env-var>
```

Add a new pipeline configuration.

**Options:**
- `--url` (required): GitLab instance URL
- `--project-id` (required): GitLab project ID
- `--token-env` (required): Environment variable name containing the GitLab token

**Example:**
```bash
bf pipeline add my-project --url https://gitlab.example.com --project-id 12345 --token-env GITLAB_TOKEN
```

#### `bf pipeline list`

```bash
bf pipeline list
```

Display all configured pipelines in a table, showing which setups use each pipeline.

#### `bf pipeline remove`

```bash
bf pipeline remove <name>
```

Remove a pipeline configuration. Fails if any setups currently reference this pipeline.

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

pipelines:
  my-project:
    url: "https://gitlab.example.com"
    project_id: 12345
    token_env: "GITLAB_TOKEN"     # env var name, NOT the token

setups:
  office-a:
    host: "10.0.0.5"
    user: "ci"
    runner: "pytest"              # default command when none given
    pipeline: my-project          # reference to pipeline config
    logs:
      remote_log_dir: ".bifrost/logs"     # relative to project root on remote
      local_log_dir: ".bifrost/office-a"

  office-b:
    host: "10.1.0.7"
    user: "ci"
    runner: "./run_tests.sh"
    pipeline: my-project          # same pipeline, different setup
    logs:
      remote_log_dir: ".bifrost/logs"
      local_log_dir: ".bifrost/office-b"

  office-c:
    host: "10.2.0.8"
    user: "ci"
    # no pipeline - runs without CI checks
```

### Config reference

| Field | Required | Description |
|-------|----------|-------------|
| `version` | yes | Must be `1` |
| `defaults.setup` | no | Setup used when `--setup` is omitted |
| `pipelines.<name>.url` | yes* | GitLab instance URL (*required if pipeline exists) |
| `pipelines.<name>.project_id` | yes* | GitLab project ID (*required if pipeline exists) |
| `pipelines.<name>.token_env` | yes* | Name of the env var holding the GitLab API token |
| `setups.<name>.host` | yes | SSH hostname or IP |
| `setups.<name>.user` | yes | SSH username |
| `setups.<name>.pipeline` | no | Reference to a pipeline configuration (enables CI checks) |
| `setups.<name>.runner` | no | Default command when no `-- <cmd>` is given |
| `setups.<name>.logs.remote_log_dir` | no | Remote log directory (default: `.bifrost/logs`) |
| `setups.<name>.logs.local_log_dir` | no | Local log directory (default: `.bifrost/<setup-name>`) |

---

## Security

- **No secrets in config files.** Tokens are read from environment variables. The config only stores the env var name (e.g. `token_env: "GITLAB_TOKEN"`).
- **SSH auth** relies entirely on your system SSH agent and `~/.ssh/config`. bifrost only stores `host` and `user`.
- Token values are never printed in output or error messages.
- **Pipeline configurations** are named and reusable - multiple setups can reference the same pipeline configuration.

---

## Run metadata

Each run produces a folder under `.bifrost/logs/<run-id>/` on the remote and `.bifrost/<setup>/<run-id>/` locally containing:

- `run.json` --- setup, ref, command, exit code, timestamp, log paths
- Any logs or output from the run

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | CI pipeline busy |
| 3 | Config error |
| 4 | SSH/connectivity error |
| 5 | Remote command failed |
| 6 | Log copy failed |

---

## Architecture

bifrost uses a vertical slice architecture with clean separation:

```
src/bifrost/
  cli/       → main app, version, error handling
  commands/  → vertical slices per feature (run, ssh, status, config, pipeline)
  shared/    → domain models, config management, errors
  infra/     → SSH, rsync, GitLab API, git operations (subprocess-based)
  di.py      → dependency injection container
```

- Each command is a self-contained vertical slice with its own logic
- Shared layer contains domain models, config management, and error types
- Infra wraps external systems (SSH, rsync, GitLab API) behind protocols for testability
- Lightweight DI container for dependency injection

### Pipeline gate

The pipeline gate is protocol-based (`PipelineGate`), currently supporting:

- `NonePipelineGate` --- always allows runs (used when setup has no pipeline configured)
- `GitLabPipelineGate` --- checks GitLab for running/pending pipelines via API

Pipeline configurations are named and managed separately from setups, allowing multiple setups to share the same pipeline configuration. Adding new providers (GitHub Actions, Jenkins, etc.) means implementing the `PipelineGate` protocol.

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

# Set up pre-commit hooks (runs ruff + mypy on every commit)
uv run pre-commit install

# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v
```

### Code quality

Linting, formatting, and type checking are enforced via [pre-commit](https://pre-commit.com/) hooks.
To run them manually:

```bash
# Lint (with auto-fix)
uv run ruff check --fix src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy

# Run all pre-commit hooks against all files
uv run pre-commit run --all-files
```

---

## Name

**Bifr&#246;st** is the bridge between worlds in Norse mythology.

> local machine &#8596; remote setups &#8596; CI environments
