"""Import and assign textures to a material."""

import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import chain
from pathlib import Path

import bpy
from bpy import props as b_p
from bpy import types as b_t
from bpy_extras.io_utils import ImportHelper

from .._helpers import log
from ..enums import BlenderOperatorReturnType, Colorspace
from ..preferences import get_preferences
from ..utils import AddonException, Registry, load_material_from_lib
from ._utils import get_selected_materials

UTIL_MATS_IMPORT_SAMPLE_NAME = "pawsbkr_texture_import_sample"


@Registry.add
class TextureImportLoadSampleMaterial(b_t.Operator):
    """Load sample material with node names setup."""

    bl_idname = "pawsbkr.texture_import_load_sample_material"
    bl_label = "Load Sample Material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: b_t.Context) -> set[BlenderOperatorReturnType]:
        """Load Sample Material."""
        load_material_from_lib(UTIL_MATS_IMPORT_SAMPLE_NAME)

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class TextureImport(b_t.Operator, ImportHelper):
    """Import and assign textures to a material."""

    bl_idname = "pawsbkr.texture_import"
    bl_label = "Import Textures"
    bl_options = {"REGISTER", "UNDO"}

    directory: b_p.StringProperty(  # type: ignore[valid-type]
        subtype="DIR_PATH",  # noqa: F821
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    files: b_p.CollectionProperty(  # type: ignore[valid-type]
        type=b_t.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    filter_folder: b_p.BoolProperty(  # type: ignore[valid-type]
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    filter_image: b_p.BoolProperty(  # type: ignore[valid-type]
        default=True,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    target_material_name: b_p.StringProperty(  # type: ignore[valid-type]
        name="Material Name",
        description="Material to set textures. All selected if empty",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    unlink_existing_textures: b_p.BoolProperty(  # type: ignore[valid-type]
        name="Unlink Existing Textures",
        description="Unlink existing textures from managed nodes",
        default=True,
    )

    def execute(self, _context: b_t.Context) -> set[BlenderOperatorReturnType]:
        """Update material textures."""
        selected_mats = tuple(get_selected_materials())

        mats: Iterable[b_t.Material]

        if self.target_material_name:
            mats = [bpy.data.materials[self.target_material_name]]
        else:
            mats = selected_mats

        for mat in mats:
            log(f"Updating material {mat.name}")
            self._update_material(mat)

        return {BlenderOperatorReturnType.FINISHED}

    def _update_material(self, mat: b_t.Material) -> None:
        pref_to_nodes = get_prefix_to_nodes_map(mat)
        if len(tuple(pref_to_nodes.nodes)) < 1:
            raise AddonException(
                f"No suitable nodes found in the material: {mat.name!r}"
            )

        assign_images_to_material(
            mat, self._load_images(mat), self.unlink_existing_textures
        )

    def _load_images(self, mat: b_t.Material) -> list[b_t.Image]:
        images: list[b_t.Image] = []

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

    by_prefix: dict[NodeNamePrefix, list[b_t.ShaderNodeTexImage]]

    @property
    def nodes(self) -> Iterable[b_t.ShaderNodeTexImage]:
        """Returns list of all nodes."""
        return chain.from_iterable(self.by_prefix.values())


def get_prefix_to_nodes_map(mat: b_t.Material) -> PrefixNodesMapping:
    """Return map of node name prefixes to nodes."""
    prefs = get_preferences()
    pref_nodes_map = PrefixNodesMapping(defaultdict(list))
    for node in mat.node_tree.nodes:
        for imp_rule in prefs.get_enabled_import_rules():
            # TODO: write test for regex
            prefix = imp_rule.node_name_prefix
            if not re.match(rf"^{prefix}([_.\-]|$)", node.name):
                continue

            if not isinstance(node, b_t.ShaderNodeTexImage):
                raise AddonException(
                    f"Node with name {node.name!r} has wrong type: "
                    f"{type(node)}. Expected: {b_t.ShaderNodeTexImage}"
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
    mat: b_t.Material,
    images: Sequence[b_t.Image],
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
