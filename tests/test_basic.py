from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from yaml_settings_pydantic import (
    DEFAULT_YAML_FILE_CONFIG_DICT,
    BaseYamlSettings,
    CreateYamlSettings,
    YamlFileConfigDict,
    YamlSettingsConfigDict,
)


class TestCreateYamlSettings:
    def test_reload(self, file_dummies: Any) -> None:
        # Test args
        with pytest.raises(ValueError):
            CreateYamlSettings(BaseYamlSettings)

        # Make sure it works. Check name of returned learcal
        def create_settings(reload: Any | None = None, files: Any | None = None) -> Any:
            return type(
                "Settings",
                (BaseYamlSettings,),
                {
                    "__yaml_reload__": reload or False,
                    "__yaml_files__": files or set(file_dummies),
                },
            )

        Settings = create_settings()
        yaml_settings = CreateYamlSettings(Settings)
        yaml_settings()
        if yaml_settings.reload:
            raise ValueError

        # Malform a file.
        bad: Path = Settings.__yaml_files__.pop()
        with bad.open("w") as file:
            yaml.dump([], file)

        # Loading should not be an error as the files should not be reloaded.
        yaml_settings()

        # Test reloading with bad file.
        # This could be called without the args as mutation is visible to fn
        Settings = create_settings()
        yaml_settings = CreateYamlSettings(Settings)

        with pytest.raises(ValueError) as err:
            yaml_settings()

        if bad.as_posix() not in str(err.value):
            raise ValueError

        with bad.open("w") as file:
            yaml.dump({}, file)

        yaml_settings()

    def from_model_config(self, **kwargs: Any) -> tuple[CreateYamlSettings, type[BaseYamlSettings]]:
        Settings = type(
            "Settings",
            (BaseYamlSettings,),
            {"model_config": YamlSettingsConfigDict(**kwargs)},  # type: ignore
        )
        return CreateYamlSettings(Settings), Settings

    def test_dunders_have_priority(self) -> None:
        init_reload = True
        foo_bar: Path = Path("foo-bar.yaml")
        yaml_settings, Settings = self.from_model_config(
            yaml_files={foo_bar},
            yaml_reload=init_reload,
        )

        default = DEFAULT_YAML_FILE_CONFIG_DICT
        if not yaml_settings.files == {foo_bar: default}:
            raise ValueError
        if not yaml_settings.reload == init_reload:
            raise ValueError

        final_files: set[Path] = {Path("spam-eggs.yaml")}
        OverwriteSettings = type(
            "OverwriteSettings",
            (Settings,),
            {"__yaml_files__": final_files},
        )
        yaml_settings = CreateYamlSettings(OverwriteSettings)

        if not yaml_settings.files == {Path("spam-eggs.yaml"): default}:
            raise ValueError
        if not yaml_settings.reload == init_reload:
            raise ValueError

    @pytest.mark.parametrize(
        "yaml_files",
        [
            Path("foo.yaml"),
            {Path("foo.yaml")},
            {Path("foo.yaml"): YamlFileConfigDict(required=True, subpath=None)},
        ],
    )
    def test_hydration_yaml_files(self, yaml_files: Any) -> None:
        make, _ = self.from_model_config(yaml_files=yaml_files)

        if not len(make.files) == 1:
            raise ValueError
        if not isinstance(make.files, dict):
            raise ValueError
        if not (foo := make.files.get(Path("foo.yaml"))):
            raise ValueError
        if not isinstance(foo, dict):
            raise ValueError
        if not foo.get("required"):
            raise ValueError
        if foo.get("subpath"):
            raise ValueError

    def test_yaml_not_required(self) -> None:
        # Should not raise error
        make, Settings = self.from_model_config(
            yaml_files={
                Path("foo.yaml"): YamlFileConfigDict(
                    required=False,
                    subpath=None,
                ),
            },
        )
        if not make.files.get(Path("foo.yaml")):
            raise ValueError
        make.load()

        # Should raise error
        make, _ = self.from_model_config(yaml_files=Path("foo.yaml"))
        with pytest.raises(ValueError) as err:
            make.load()

        if not str(err.value):
            raise ValueError
