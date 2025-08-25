"""Addon operators."""

from .bake_selected import BakeSelected
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
from .texture_set_material_create import TextureSetMaterialCreate
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

__all__ = [
    "BakeSelected",
    "DebugResetState",
    "MaterialCleanupSelected",
    "MaterialSetup",
    "MaterialSetupSelected",
    "RandomizeColor",
    "TextureImport",
    "TextureImportLoadSampleMaterial",
    "TextureSetAdd",
    "TextureSetBake",
    "TextureSetMaterialCreate",
    "TextureSetMeshAdd",
    "TextureSetMeshClear",
    "TextureSetMeshRemove",
    "TextureSetRemove",
    "TextureSetTextureAdd",
    "TextureSetTextureCleanupMaterial",
    "TextureSetTextureRemove",
    "TextureSetTextureSetupMaterial",
]
