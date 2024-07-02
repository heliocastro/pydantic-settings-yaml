from __future__ import annotations

import click

from yaml_settings_pydantic import __version__


@click.command
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="YAML Settings Pydantic",
    message="%(prog)s version %(version)s",
)
def main() -> None:
    pass


if __name__ == "__main__":
    main()
