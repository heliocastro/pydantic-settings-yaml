from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from pydantic_settings import SettingsConfigDict
from typing_extensions import LiteralString

from .examples import ExplicitSettings, MinimalSettings, SubpathSettings


@pytest.mark.parametrize(
    "Settings",
    [ExplicitSettings, MinimalSettings, SubpathSettings],
)
class TestExampleCanOverWrite:
    env_extras = {
        "MY_SETTINGS_MYFIRSTSETTING": "9999",
        "MY_SETTINGS_MYDATABASESETTINGS__HOSTSPEC__HOST": "12.34.56.78",
    }

    def test_init(self, Settings: type[Any]) -> None:
        raw = {
            "myFirstSetting": 1234,
            "myDatabaseSettings": {
                "connectionspec": {},
                "hostspec": {
                    "username": "cornpuff",
                    "password": "the thing, you know, the thing",
                },
            },
        }
        s = Settings(**raw)

        if not s.myFirstSetting == 1234:
            raise ValueError("Failed to load first level settings.")
        if not s.myDatabaseSettings.hostspec.username == "cornpuff":
            raise ValueError("Failed to load nested configuration.")

    @mock.patch.dict(os.environ, **env_extras)
    def test_envvars(self, Settings: type[Any]) -> None:
        """Environment variables should be able to overwrite YAML
        configuration."""

        s = Settings()
        expected = self.env_extras["MY_SETTINGS_MYFIRSTSETTING"]
        if not s.myFirstSetting == int(expected):
            raise ValueError

        field = "MY_SETTINGS_MYDATABASESETTINGS__HOSTSPEC__HOST"
        expected = self.env_extras[field]
        if not s.myDatabaseSettings.hostspec.host == expected:
            raise ValueError

    @mock.patch.dict(os.environ, **env_extras)
    def test_envvars_after_init(self, Settings: type[Any]) -> None:
        """Environment variables should take presendence by init."""

        expectedMyFirstSetting = 11111111
        s = Settings(myFirstSetting=expectedMyFirstSetting)
        if not s.myFirstSetting == expectedMyFirstSetting:
            raise ValueError

    def test_dotenv(self, Settings: type[Any]) -> None:
        model_config = SettingsConfigDict(
            env_prefix="MY_SETTINGS_",
            env_nested_delimiter="__",
            env_file=Path(__file__).parent / "examples" / "example.env",
        )
        namespace = {"model_config": model_config}
        SettingsWEnv = type("ExplicitSettingsWEnv", (Settings,), namespace)
        s = SettingsWEnv()
        if not s.myFirstSetting == 8888:
            raise ValueError
        if not s.myDatabaseSettings.hostspec.host == "5.4.3.2":
            raise ValueError


@pytest.mark.parametrize(
    "subcommand",
    ["minimal-settings", "explicit-settings", "subpath-settings"],
)
def test_example_execution(subcommand: str | None) -> None:
    command = ["python", "-m", "tests.examples"]
    if subcommand is not None:
        command.append(subcommand)
    result = subprocess.run(  # noqa: S603
        command,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )
    out: str | list[LiteralString] | list[str]
    if not result.returncode == 0:
        raise ValueError

    if not (out := result.stdout.decode()):
        raise ValueError

    out = out.split("\n")
    if "=============" not in out[0]:
        raise ValueError
    if "=============" not in out[-2]:
        raise ValueError
    if "Result" not in out[1]:
        raise ValueError

    try:
        # Verify that the body is valid JSON
        result = json.loads("".join(out[2:-2]))
    except json.JSONDecodeError as e:
        print(e.msg)
