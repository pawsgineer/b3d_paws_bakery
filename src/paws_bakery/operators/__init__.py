"""Addon operators."""

from .bake import Bake
from .debug import DebugResetState
from .material_setup import (
    MaterialCleanupSelected,
    MaterialSetup,
    MaterialSetupSelected,
)
from .randomize_color import RandomizeColor
from .texture_import import TextureImport, TextureImportLoadSampleMaterial
from .texture_set import TextureSetAdd, TextureSetRemove
from .texture_set_bake import TextureSetBake
from .texture_set_mesh import (
    TextureSetMeshAdd,
    TextureSetMeshClear,
    TextureSetMeshRemove,
)
from .texture_set_texture import (
    TextureSetTextureAdd,
    TextureSetTextureCleanupMaterial,
    TextureSetTextureRemove,
    TextureSetTextureSetupMaterial,
)
from .texture_set_texture_bake import TextureSetTextureBake

__all__ = [
    "Bake",
    "DebugResetState",
    "MaterialCleanupSelected",
    "MaterialSetup",
    "MaterialSetupSelected",
    "RandomizeColor",
    "TextureImport",
    "TextureImportLoadSampleMaterial",
    "TextureSetAdd",
    "TextureSetBake",
    "TextureSetMeshAdd",
    "TextureSetMeshClear",
    "TextureSetMeshRemove",
    "TextureSetRemove",
    "TextureSetTextureAdd",
    "TextureSetTextureBake",
    "TextureSetTextureCleanupMaterial",
    "TextureSetTextureRemove",
    "TextureSetTextureSetupMaterial",
]
