"""Import and assign textures to a material."""

from pathlib import Path
from typing import Sequence

import bpy
from bpy import props as b_p
from bpy import types as b_t
from bpy_extras.io_utils import ImportHelper

from .._helpers import UTIL_MATS_PATH, log
from ..enums import BlenderOperatorReturnType, Colorspace
from ..props_enums import TextureTypeAlias
from ..utils import AddonException, Registry
from ._utils import get_selected_materials

UTIL_MATS_IMPORT_SAMPLE_NAME = "pawsbkr_texture_import_sample"


@Registry.add
class TextureImportLoadSampleMaterial(b_t.Operator):
    """Load sample material with node names setup."""

    bl_idname = "pawsbkr.texture_import_load_sample_material"
    bl_label = "Load Sample Material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: b_t.Context):
        """Load Sample Material."""
        if bpy.data.materials.get(UTIL_MATS_IMPORT_SAMPLE_NAME) is not None:
            self.report(
                {"ERROR"},
                f"Material with the name {UTIL_MATS_IMPORT_SAMPLE_NAME!r} "
                "already exists. "
                "Remove or rename it if you want to reimport sample material",
            )
            return {BlenderOperatorReturnType.CANCELLED}

        with bpy.data.libraries.load(
            str(UTIL_MATS_PATH),
            link=False,
            assets_only=True,
        ) as (data_src, data_dst):
            if UTIL_MATS_IMPORT_SAMPLE_NAME not in data_src.materials:
                raise AddonException(
                    f"No material with name {UTIL_MATS_IMPORT_SAMPLE_NAME!r} found"
                )
            data_dst.materials = [UTIL_MATS_IMPORT_SAMPLE_NAME]

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureImport(b_t.Operator, ImportHelper):
    """Import and assign textures to a material."""

    bl_idname = "pawsbkr.texture_import"
    bl_label = "Import Textures"
    bl_options = {"REGISTER", "UNDO"}

    directory: b_p.StringProperty(
        subtype="FILE_PATH",  # noqa: F821
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    files: b_p.CollectionProperty(
        type=b_t.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    filter_folder: b_p.BoolProperty(
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    filter_image: b_p.BoolProperty(
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    target_material_name: b_p.StringProperty(
        name="Material Name",
        description="Material to set textures. All selected if empty",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    unlink_existing_textures: b_p.BoolProperty(
        name="Unlink Existing Textures",
        description="Unlink existing textures from managed nodes",
        default=True,
    )

    def execute(self, context: b_t.Context):
        """Update material textures."""
        selected_mats = get_selected_materials()

        mats: Sequence[b_t.Material]

        if self.target_material_name:
            mats = [bpy.data.materials[self.target_material_name]]
        else:
            mats = selected_mats.values()

        for mat in mats:
            log(f"Updating material {mat.name}")
            self.update_material(context, mat)

        return {BlenderOperatorReturnType.FINISHED}

    def update_material(self, _context: b_t.Context, mat: b_t.Material):
        """Update material textures using node name prefix matching."""
        # Build a mapping from TextureTypeAlias to all matching nodes (by prefix)
        node_map = {}
        for tex_type in TextureTypeAlias:
            prefix = tex_type.node_name
            node_map[tex_type] = [
                node for node in mat.node_tree.nodes if node.name.startswith(prefix)
            ]

        if self.unlink_existing_textures:
            for nodes in node_map.values():
                for node in nodes:
                    node.image = None

        for file in self.files:
            image_tex_type = TextureTypeAlias.check_type(file.name)
            if image_tex_type is None:
                log(f"Unrecognized texture type: {file.name!r}")
                continue

            nodes = node_map.get(image_tex_type, [])
            if not nodes:
                log(f"No node found for texture type {image_tex_type!r}. Ignoring")
                continue

            log(f"Importing texture {file.name!r} to nodes {[n.name for n in nodes]!r}")

            image = bpy.data.images.load(
                bpy.path.relpath(str(Path(self.directory, file.name))),
                check_existing=True,
            )
            if image_tex_type not in [
                TextureTypeAlias.ALBEDO,
                TextureTypeAlias.EMISSION,
            ]:
                image.colorspace_settings.name = Colorspace.NON_COLOR

            for node in nodes:
                node.image = image

        # Optionally mute nodes with no image
        for nodes in node_map.values():
            for node in nodes:
                node.mute = node.image is None
