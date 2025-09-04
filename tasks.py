# pylint: disable=missing-module-docstring,missing-class-docstring,unused-argument
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import invoke
from dotenv import dotenv_values

EXTENSION_NAME = "paws_bakery"
DOTENV_PATH = Path(".env")
SRC_DIR = Path("./src", EXTENSION_NAME)

assert DOTENV_PATH.exists()
assert SRC_DIR.exists()

EXT_VERSION: str
with open(SRC_DIR.joinpath("blender_manifest.toml"), "rb") as f:
    data = tomllib.load(f)
    EXT_VERSION = data["version"]


_AvailableVersionsType = Literal["5.0", "4.5", "4.4", "4.3", "4.2"]


@dataclass(kw_only=True, frozen=True)
class Config:
    blender_version: _AvailableVersionsType = "4.5"
    blender_pathes: dict[_AvailableVersionsType, Path]
    zip_path: Path

    @property
    def blender_path(self) -> Path:
        return cfg.blender_pathes[cfg.blender_version]

    def ensure_blender_path_valid(self) -> None:
        print("cfg.blender_path", cfg.blender_path)
        assert cfg.blender_path.is_file()
        assert os.access(cfg.blender_path, os.X_OK)


def is_executable_path_valid(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _default_str(name: str, default: str = "") -> str:
    return cast(str, dotenv_vars.get(name, default))


dotenv_vars = {
    **dotenv_values(DOTENV_PATH, verbose=True),
    **os.environ,
}

cfg = Config(
    blender_version=_default_str("PBKR_BLENDER_VERSION", "4.5"),
    blender_pathes={
        "5.0": Path(_default_str("PBKR_BLENDER_PATH_5_0")),
        "4.5": Path(_default_str("PBKR_BLENDER_PATH_4_5")),
        "4.4": Path(_default_str("PBKR_BLENDER_PATH_4_4")),
        "4.3": Path(_default_str("PBKR_BLENDER_PATH_4_3")),
        "4.2": Path(_default_str("PBKR_BLENDER_PATH_4_2")),
    },
    zip_path=Path(_default_str("PBKR_ZIP_PATH", f"{EXTENSION_NAME}-{EXT_VERSION}.zip")),
)


VERSION_CMD: list[str] = [
    str(cfg.blender_path),
    "--version",
]

BUILD_CMD: list[str] = [
    str(cfg.blender_path),
    "--factory-startup",
    "--command",
    "extension",
    "build",
    "--verbose",
    "--source-dir",
    str(SRC_DIR),
    "--output-filepath",
    str(cfg.zip_path),
]

INSTALL_CMD: list[str] = [
    str(cfg.blender_path),
    "--factory-startup",
    "--command",
    "extension",
    "install-file",
    "-r",
    "user_default",
    "-e",
    str(cfg.zip_path),
]

LAUNCH_CMD: list[str] = [
    str(cfg.blender_path),
    "--python",
    "./.vscode/enable_faulthandler.py",
]

LAUNCH_TEST_CMD: list[str] = [
    str(cfg.blender_path),
    "./tests/test_bl/test_01.blend",
    "--python-exit-code",
    "1",
    "--debug-python",
    "--python",
    "./tests/test_bl/bl_script.py",
    "-p",
    "0 0 10 10",
    "--no-window-focus",
    "2>&1",
]


@invoke.tasks.task
def available_versions(ctx: invoke.context.Context) -> None:
    """Print Blender versions found in envvars."""
    for ver, path in cfg.blender_pathes.items():
        print(
            f"Version {ver!r} path:", path if is_executable_path_valid(path) else None
        )


@invoke.tasks.task()
def version(ctx: invoke.context.Context) -> None:
    """Print Blender version."""
    cfg.ensure_blender_path_valid()

    ctx.run(" ".join(VERSION_CMD))


@invoke.tasks.task()
def build(ctx: invoke.context.Context) -> None:
    """Build extension."""
    cfg.ensure_blender_path_valid()

    ctx.run(" ".join(BUILD_CMD))


@invoke.tasks.task()
def install(ctx: invoke.context.Context) -> None:
    """Install extension."""
    cfg.ensure_blender_path_valid()

    ctx.run(" ".join(INSTALL_CMD))


@invoke.tasks.task()
def launch(
    ctx: invoke.context.Context,
    factory_startup: bool = False,
) -> None:
    """Launch blender."""
    cfg.ensure_blender_path_valid()

    cmd = LAUNCH_CMD[:]
    if factory_startup:
        cmd.append(" --factory-startup")

    ctx.run(" ".join(cmd))


@invoke.tasks.task(name="open", help={"file": "Path to .blend file."})
def open_blendfile(
    ctx: invoke.context.Context,
    file: str,
    factory_startup: bool = False,
) -> None:
    """Open file in blender."""
    cfg.ensure_blender_path_valid()

    cmd = LAUNCH_CMD[:]
    if factory_startup:
        cmd.append(" --factory-startup")
    if file:
        cmd.append(f" {file}")

    ctx.run(" ".join(cmd))


@invoke.tasks.task()
def launch_test(ctx: invoke.context.Context) -> None:
    """Launch blender."""
    cfg.ensure_blender_path_valid()

    ctx.run(" ".join(LAUNCH_TEST_CMD))
