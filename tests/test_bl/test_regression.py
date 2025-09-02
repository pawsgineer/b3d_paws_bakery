from pathlib import Path

import pytest
import syrupy
from syrupy.extensions.image import PNGImageSnapshotExtension

TEX_DIR = Path("./tests/test_bl/pawsbkr_textures")
TEX_SET_01_NAME = "test_set_01"
TEX_SET_01_DIR = TEX_DIR.joinpath(Path(TEX_SET_01_NAME))
TEX_SIZE = 64

img_names = [
    "ao",
    "aorm",
    "color",
    "combined",
    "diffuse",
    "emit",
    "env",
    "glossy",
    "grid_color",
    "grid_uv",
    "matid",
    "metalness",
    "normalgl",
    "opacity",
    "position",
    "roughness_native",
    "roughness",
    "shadow",
    "transmission",
    "uv",
]


@pytest.fixture
def snapshot_png(snapshot: syrupy.assertion.SnapshotAssertion):
    # return snapshot.use_extension(PNGImageSnapshotExtension)
    return snapshot(extension_class=PNGImageSnapshotExtension)


def test_dirs():
    assert TEX_DIR.exists()
    assert TEX_SET_01_DIR.exists()


def get_image_filename(suffix: str) -> str:
    return f"{TEX_SET_01_NAME}_{TEX_SIZE}_{suffix}.png"


@pytest.mark.parametrize("name", img_names)
def test_existence(name):
    assert TEX_SET_01_DIR.joinpath(get_image_filename(name)).exists()


@pytest.mark.parametrize("name", img_names)
def test_image(name, snapshot_png):
    with open(TEX_SET_01_DIR.joinpath(get_image_filename(name)), "rb") as img:
        assert img.read() == snapshot_png
