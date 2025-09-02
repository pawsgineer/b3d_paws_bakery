# flake8: noqa: F821
"""Import and assign textures to a material."""

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import chain
from pathlib import Path

import bpy
from bpy import props as blp
from bpy import types as blt
from bpy_extras.io_utils import ImportHelper

from .._helpers import log
from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderOperatorType as BOT
from ..enums import Colorspace
from ..preferences import get_preferences
from ..utils import AddonException, AssetLibraryManager, Registry
from ._utils import get_selected_materials

UTIL_MATS_IMPORT_SAMPLE_NAME = "pawsbkr_texture_import_sample"


@Registry.add
class TextureImportLoadSampleMaterial(blt.Operator):
    """Load sample material with node names setup."""

    bl_idname = "pawsbkr.texture_import_load_sample_material"
    bl_label = "Load Sample Material"
    bl_options = {BOT.REGISTER, BOT.UNDO}

    def execute(self, _context: blt.Context) -> set[BORT]:
        """Load Sample Material."""
        AssetLibraryManager.material_load(UTIL_MATS_IMPORT_SAMPLE_NAME)

        return {BORT.FINISHED}


@Registry.add
class TextureImport(blt.Operator, ImportHelper):
    """Import and assign textures to a material."""

    bl_idname = "pawsbkr.texture_import"
    bl_label = "Import Textures"
    bl_options = {BOT.REGISTER, BOT.UNDO}

    directory: blp.StringProperty(  # type: ignore[valid-type]
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )
    files: blp.CollectionProperty(  # type: ignore[valid-type]
        type=blt.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    filter_folder: blp.BoolProperty(  # type: ignore[valid-type]
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    filter_image: blp.BoolProperty(  # type: ignore[valid-type]
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    target_material_name: blp.StringProperty(  # type: ignore[valid-type]
        name="Material Name",
        description="Material to set textures. All selected if empty",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    unlink_existing_textures: blp.BoolProperty(  # type: ignore[valid-type]
        name="Unlink Existing Textures",
        description="Unlink existing textures from managed nodes",
        default=True,
    )

    def execute(self, _context: blt.Context) -> set[BORT]:
        """Update material textures."""
        selected_mats = tuple(get_selected_materials())

        mats: Iterable[blt.Material]

        if self.target_material_name:
            mats = [bpy.data.materials[self.target_material_name]]
        else:
            mats = selected_mats

        for mat in mats:
            log(f"Updating material {mat.name}")
            self._update_material(mat)

        return {BORT.FINISHED}

    def _update_material(self, mat: blt.Material) -> None:
        pref_to_nodes = get_prefix_to_nodes_map(mat)
        if len(tuple(pref_to_nodes.nodes)) < 1:
            raise AddonException(
                f"No suitable nodes found in the material: {mat.name!r}"
            )

        assign_images_to_material(
            mat, self._load_images(mat), self.unlink_existing_textures
        )

    def _load_images(self, mat: blt.Material) -> list[blt.Image]:
        images: list[blt.Image] = []

        prefs = get_preferences()

        pref_to_nodes = get_prefix_to_nodes_map(mat)

        for file in self.files:
            imp_rule = prefs.get_matching_import_rule(file.name)
            if imp_rule is None:
                log(f"Unrecognized texture type: {file.name!r}")
                continue

            nodes = pref_to_nodes.by_prefix[imp_rule.node_name_prefix]
            if not nodes:
                log(f"No node found for texture type {imp_rule!r}. Ignoring")
                continue

            image = bpy.data.images.load(
                bpy.path.relpath(str(Path(self.directory, file.name))),
                check_existing=True,
            )
            images.append(image)
            if imp_rule.is_non_color:
                image.colorspace_settings.name = Colorspace.NON_COLOR

        return images


NodeNamePrefix = str


@dataclass
class PrefixNodesMapping:
    """Container for map of low to high Object names."""

    by_prefix: dict[NodeNamePrefix, list[blt.ShaderNodeTexImage]]

    @property
    def nodes(self) -> Iterable[blt.ShaderNodeTexImage]:
        """Returns list of all nodes."""
        return chain.from_iterable(self.by_prefix.values())


def get_prefix_to_nodes_map(mat: blt.Material) -> PrefixNodesMapping:
    """Return map of node name prefixes to nodes."""
    prefs = get_preferences()
    pref_nodes_map = PrefixNodesMapping(defaultdict(list))
    for node in mat.node_tree.nodes:
        for imp_rule in prefs.get_enabled_import_rules():
            # TODO: write test for regex
            prefix = imp_rule.node_name_prefix
            if not re.match(rf"^{prefix}([_.\-]|$)", node.name):
                continue

            if not isinstance(node, blt.ShaderNodeTexImage):
                raise AddonException(
                    f"Node with name {node.name!r} has wrong type: "
                    f"{type(node)}. Expected: {blt.ShaderNodeTexImage}"
                )

            pref_nodes_map.by_prefix[prefix].append(node)

    pref_nodes_map.by_prefix.update(
        {
            ta_props.node_name_prefix: []
            for ta_props in prefs.get_enabled_import_rules()
            if ta_props.node_name_prefix not in pref_nodes_map.by_prefix
        }
    )

    return pref_nodes_map


def assign_images_to_material(
    mat: blt.Material,
    images: Sequence[blt.Image],
    unlink_existing: bool,
) -> None:
    """Assign images to material texture nodes."""
    prefs = get_preferences()

    pref_to_nodes = get_prefix_to_nodes_map(mat)

    if len(tuple(pref_to_nodes.nodes)) < 1:
        raise AddonException(f"No suitable nodes found in the material: {mat.name!r}")

    if unlink_existing:
        for node in pref_to_nodes.nodes:
            node.image = None  # type: ignore[assignment]

    for img in images:
        imp_rule = prefs.get_matching_import_rule(img.filepath)
        if imp_rule is None:
            log(f"Unrecognized texture type for image: {img.filepath!r}")
            continue

        prefix = imp_rule.node_name_prefix
        nodes = pref_to_nodes.by_prefix[prefix]
        if not nodes:
            log(f"No node found for texture prefix {prefix!r}. Ignoring")
            continue

        log(f"Importing texture {img.name!r} to nodes {[n.name for n in nodes]!r}")

        for node in nodes:
            node.image = img

    for node in pref_to_nodes.nodes:
        node.mute = node.image is None
