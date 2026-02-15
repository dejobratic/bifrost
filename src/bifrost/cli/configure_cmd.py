from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from bifrost.cli.app import app
from bifrost.core.configure import build_config, load_existing_config, write_config
from bifrost.core.models import ArtifactsConfig, GitLabConfig, SetupConfig

console = Console()


def _ask(prompt: str, *, default: str | None = None) -> str:
    if default is not None:
        return Prompt.ask(prompt, default=default)
    return Prompt.ask(prompt)


def _prompt_setup(
    existing: SetupConfig | None = None,
) -> tuple[str, SetupConfig]:
    name = _ask("Setup name", default=existing.name if existing else None)
    host = _ask("Host", default=existing.host if existing else None)
    user = _ask("User", default=existing.user if existing else None)
    runner_input = _ask(
        "Runner command (optional)",
        default=existing.runner or "" if existing else "",
    )
    runner = runner_input.strip() or None

    custom_artifacts = False
    if existing and existing.artifacts != ArtifactsConfig():
        custom_artifacts = Confirm.ask("Keep custom artifact dirs?", default=True)
    elif Confirm.ask("Customize artifact directories?", default=False):
        custom_artifacts = True

    if custom_artifacts:
        remote_dir = _ask(
            "Remote artifact dir",
            default=existing.artifacts.remote_dir if existing else ".bifrost",
        )
        local_dir = _ask(
            "Local artifact dir",
            default=existing.artifacts.local_dir if existing else f".bifrost/{name}",
        )
        artifacts = ArtifactsConfig(remote_dir=remote_dir, local_dir=local_dir)
    else:
        artifacts = ArtifactsConfig()

    setup = SetupConfig(
        name=name, host=host, user=user, runner=runner, artifacts=artifacts
    )
    return name, setup


def _prompt_gitlab(existing: GitLabConfig | None = None) -> GitLabConfig | None:
    if not Confirm.ask("Configure GitLab integration?", default=existing is not None):
        return None

    url = _ask("GitLab URL", default=existing.url if existing else None)

    while True:
        raw_id = _ask(
            "Project ID",
            default=str(existing.project_id) if existing else None,
        )
        try:
            project_id = int(raw_id)
            break
        except ValueError:
            console.print("[red]Project ID must be an integer.[/red]")

    token_env = _ask(
        "Token env var name",
        default=existing.token_env if existing else "GITLAB_TOKEN",
    )
    return GitLabConfig(url=url, project_id=project_id, token_env=token_env)


def _show_setups_table(setups: dict[str, SetupConfig], default: str | None) -> None:
    table = Table(title="Current Setups")
    table.add_column("Setup", style="bold")
    table.add_column("Host")
    table.add_column("User")
    table.add_column("Runner")
    table.add_column("Default", justify="center")

    for name, s in setups.items():
        table.add_row(
            name,
            s.host,
            s.user,
            s.runner or "[dim]-[/dim]",
            "[green]*[/green]" if name == default else "",
        )
    console.print(table)


def _new_config_flow() -> None:
    console.print("[bold]No existing configuration found. Let's create one.[/bold]\n")

    setups: dict[str, SetupConfig] = {}

    while True:
        name, setup = _prompt_setup()
        setups[name] = setup
        console.print()
        if not Confirm.ask("Add another setup?", default=False):
            break

    gitlab = _prompt_gitlab()

    default_setup: str | None = None
    if len(setups) > 1:
        names = list(setups.keys())
        default_setup = Prompt.ask(
            "Default setup",
            choices=names,
            default=names[0],
        )

    config = build_config(setups, default_setup=default_setup, gitlab=gitlab)
    path = write_config(config)
    console.print(f"\n[green]Configuration written to {path}[/green]")


def _existing_config_flow() -> None:
    config = load_existing_config()
    assert config is not None

    setups = dict(config.setups)
    default_setup = config.default_setup
    gitlab = config.gitlab

    _show_setups_table(setups, default_setup)
    console.print()

    actions = ["add", "modify", "remove", "gitlab", "default", "done"]

    while True:
        action = Prompt.ask(
            "Action",
            choices=actions,
            default="done",
        )

        if action == "done":
            break

        if action == "add":
            name, setup = _prompt_setup()
            setups[name] = setup

        elif action == "modify":
            names = list(setups.keys())
            target = Prompt.ask("Setup to modify", choices=names)
            old_name, old_setup = target, setups[target]
            new_name, new_setup = _prompt_setup(existing=old_setup)
            if new_name != old_name:
                del setups[old_name]
                if default_setup == old_name:
                    default_setup = new_name
            setups[new_name] = new_setup

        elif action == "remove":
            if len(setups) <= 1:
                console.print("[red]Cannot remove the last setup.[/red]")
                continue
            names = list(setups.keys())
            target = Prompt.ask("Setup to remove", choices=names)
            del setups[target]
            if default_setup == target:
                default_setup = None
                console.print("[yellow]Default setup was cleared.[/yellow]")

        elif action == "gitlab":
            gitlab = _prompt_gitlab(existing=gitlab)

        elif action == "default":
            names = list(setups.keys())
            default_setup = Prompt.ask(
                "Default setup",
                choices=names,
                default=names[0],
            )

        _show_setups_table(setups, default_setup)
        console.print()

    config = build_config(setups, default_setup=default_setup, gitlab=gitlab)
    path = write_config(config)
    console.print(f"\n[green]Configuration written to {path}[/green]")


@app.command()
def configure() -> None:
    """Interactively create or update the global Bifrost configuration."""
    existing = load_existing_config()
    if existing is None:
        _new_config_flow()
    else:
        _existing_config_flow()
