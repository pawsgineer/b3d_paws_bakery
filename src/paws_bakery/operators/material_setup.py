"""Setup material utils."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, TypeVar, cast

import bpy
from bpy import props as b_p
from bpy import types as b_t
from mathutils import Vector

from .._helpers import log
from ..enums import BlenderOperatorReturnType
from ..props import BakeSettings, BakeTextureType, get_bake_settings
from ..utils import (
    UTIL_NODES_GROUP_AORM,
    UTIL_NODES_GROUP_COLOR,
    AddonException,
    AssetLibraryManager,
    Registry,
)
from ._utils import generate_color_set, get_selected_materials

MAP_PREFIX = "pawsbkr_map_"
NODE_PREFIX = "pawsbkr_utils_"


class MaterialNodeNames(str, Enum):
    """Managed material node names."""

    @staticmethod
    def _generate_next_value_(
        name: str, _start: int, _count: int, _last_values: list[Any]
    ) -> Any:
        return NODE_PREFIX + name

    AO = auto()
    BAKE_TEXTURE = auto()
    COLOR = auto()
    COMBINE_COLOR = auto()
    FRAME = auto()
    OBJECT_INFO = auto()
    BAKE_OUT = auto()
    UV_TEXTURE = auto()
    VALUE = auto()

    #     def __new__(cls, name):
    #         obj = str.__new__(cls, NODE_PREFIX + name)
    #         obj._value_ = NODE_PREFIX + name
    #
    #         return obj

    def __str__(self) -> str:
        """Return a string representation of the Material Node name."""
        return str(self.value)


@dataclass(kw_only=True)
class TextureSize:
    """Texture size dataclass."""

    width: int
    height: int


def _get_uv_grid_map_name(texture_size: TextureSize) -> str:
    uv_size = f"{texture_size.width}_{texture_size.height}"
    return f"{MAP_PREFIX}uv_{uv_size}"


def _get_color_grid_map_name(texture_size: TextureSize) -> str:
    uv_size = f"{texture_size.width}_{texture_size.height}"
    return f"{MAP_PREFIX}color_{uv_size}"


def _init_uv_maps(texture_size: TextureSize) -> None:
    """Create uv map images."""
    uv_grid_map_name = _get_uv_grid_map_name(texture_size)
    if bpy.data.images.get(uv_grid_map_name) is None:
        bpy.ops.image.new(
            name=uv_grid_map_name,
            width=texture_size.width,
            height=texture_size.height,
            generated_type="UV_GRID",
        )
    color_grid_map_name = _get_color_grid_map_name(texture_size)
    if bpy.data.images.get(color_grid_map_name) is None:
        bpy.ops.image.new(
            name=color_grid_map_name,
            width=texture_size.width,
            height=texture_size.height,
            generated_type="COLOR_GRID",
        )


def _node_get_or_create(
    tree: b_t.ShaderNodeTree,
    name: MaterialNodeNames,
    node_type: type[ShaderNodeSub],
    parent: b_t.Node,
    location: tuple[int, int],
) -> ShaderNodeSub:
    node = tree.nodes.get(name)
    if node is not None and not isinstance(node, node_type):
        tree.nodes.remove(node)
    if node is None:
        node = cast(ShaderNodeSub, tree.nodes.new(node_type.__name__))
        node.name = node.label = name
        node.parent = parent
        node.location = location

    return cast(ShaderNodeSub, node)


BakeConnectionSocket = (
    b_t.NodeSocketFloat
    | b_t.NodeSocketVector
    | b_t.NodeSocketFloatFactor
    | b_t.NodeSocketColor
)


ShaderNodeSub = TypeVar("ShaderNodeSub", bound=b_t.ShaderNode)


class BakeMaterialManager:
    """Prepare material for baking."""

    mat: b_t.Material
    bake_settings: BakeSettings
    mat_id_color: tuple[float, float, float]

    frame: b_t.NodeFrame
    tree: b_t.ShaderNodeTree
    links: b_t.NodeLinks
    start_location: Vector
    output_node: b_t.ShaderNodeOutputMaterial

    ng_color: b_t.ShaderNodeGroup
    ng_aorm: b_t.ShaderNodeGroup

    def _add_node(self, node_type: type[ShaderNodeSub], name: str) -> ShaderNodeSub:
        if name in self.tree.nodes:
            raise AddonException(f"Material already has Node with name {name!r}")
        node: ShaderNodeSub = cast(
            ShaderNodeSub, self.tree.nodes.new(node_type.__name__)
        )
        node.name = name
        node.parent = self.frame
        node.location = self.start_location
        self.start_location.y += 250
        return node

    def _get_node_frame(self) -> b_t.NodeFrame:
        frame_name = MaterialNodeNames.FRAME
        node: b_t.Node = self.tree.nodes.get(frame_name)
        if node is not None:
            if isinstance(node, b_t.NodeFrame):
                return node
            self.tree.nodes.remove(node)

        node = cast(b_t.NodeFrame, self.tree.nodes.new(b_t.NodeFrame.__name__))
        node.name = frame_name
        node.label = "PAWS: Bakery Utils"
        node.use_custom_color = True
        node.color.hsv = (0.25, 0.7, 0.7)

        return node

    def _get_node_bake_texture(self) -> b_t.ShaderNodeTexImage:
        return _node_get_or_create(
            self.tree,
            MaterialNodeNames.BAKE_TEXTURE,
            b_t.ShaderNodeTexImage,
            self.frame,
            (800, 600),
        )

    def _get_node_bake_output(self) -> b_t.ShaderNodeOutputMaterial:
        node = _node_get_or_create(
            self.tree,
            MaterialNodeNames.BAKE_OUT,
            b_t.ShaderNodeOutputMaterial,
            self.frame,
            (800, 800),
        )
        self.tree.nodes.active = node
        return node

    def _add_color_node_group(self) -> b_t.ShaderNodeGroup:
        group = self._add_node(b_t.ShaderNodeGroup, UTIL_NODES_GROUP_COLOR)
        group.node_tree = bpy.data.node_groups.get(UTIL_NODES_GROUP_COLOR)
        group.inputs["color"].default_value = tuple(self.mat_id_color) + (1.0,)
        return group

    def _add_aorm_node_group(self) -> b_t.ShaderNodeGroup:
        group = self._add_node(b_t.ShaderNodeGroup, UTIL_NODES_GROUP_AORM)
        group.node_tree = bpy.data.node_groups.get(UTIL_NODES_GROUP_AORM)
        return group

    def _get_og_output_node(self) -> b_t.ShaderNodeOutputMaterial:
        # TODO: filter muted and not connected out nodes
        output_nodes = []
        for node in self.tree.nodes:
            if (
                node.name == MaterialNodeNames.BAKE_OUT
                or not isinstance(node, b_t.ShaderNodeOutputMaterial)
                or node.target not in ("CYCLES", "ALL")
            ):
                continue
            output_nodes.append(node)

        # TODO: we shouldn't care about existing material outputs when baking matid?
        if not output_nodes:
            raise AddonException("Can't bake material without material outputs")

        if len(output_nodes) > 1:
            raise AddonException("Material has more than 1 material output")

        return output_nodes[0]

    def _get_shader_node(self) -> b_t.ShaderNodeBsdfPrincipled:
        node = self._get_og_output_node().inputs["Surface"].links[0].from_node

        # TODO: add more shader types?
        if not isinstance(node, b_t.ShaderNodeBsdfPrincipled):
            raise AddonException("Can't bake material with current shader type")

        return node

    def _set_up_link(
        self,
        input_socket: BakeConnectionSocket,
        output_socket: BakeConnectionSocket | b_t.NodeSocketShader,
        default_value: float | Sequence[float] | None = None,
        default_input_socket: BakeConnectionSocket | None = None,
        default_output_socket: BakeConnectionSocket | None = None,
    ) -> None:
        if input_socket.is_linked:
            self.links.new(input_socket.links[0].from_socket, output_socket)
            return

        if default_value is None:
            return
        if default_input_socket is None:
            default_input_socket = input_socket

        if type(default_input_socket.default_value) is not type(default_value):
            raise AddonException(
                "Socket type and default value doesn't match",
                type(default_input_socket.default_value),
                type(default_value),
            )

        default_input_socket.default_value = default_value
        if default_output_socket:
            self.links.new(default_output_socket, output_socket)

    def _set_up_ao(
        self,
        shader_node: b_t.ShaderNodeBsdfPrincipled,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        self.links.new(self.ng_aorm.outputs["ao"], bake_out_node.inputs["Surface"])

        s_inp = shader_node.inputs["Normal"]
        s_out = self.ng_aorm.inputs["normal"]
        assert isinstance(s_inp, b_t.NodeSocketVector), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketVector), type(s_out)
        self._set_up_link(s_inp, s_out)

    def _set_up_aorm(
        self,
        shader_node: b_t.ShaderNodeBsdfPrincipled,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        self.links.new(self.ng_aorm.outputs["aorm"], bake_out_node.inputs["Surface"])

        s_inp = shader_node.inputs["Normal"]
        s_out = self.ng_aorm.inputs["normal"]
        assert isinstance(s_inp, b_t.NodeSocketVector), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketVector), type(s_out)
        self._set_up_link(s_inp, s_out)

        s_inp = shader_node.inputs["Roughness"]
        s_out = self.ng_aorm.inputs["roughness"]
        assert isinstance(s_inp, b_t.NodeSocketFloatFactor), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketFloatFactor), type(s_out)
        self._set_up_link(s_inp, s_out, s_inp.default_value)

        s_inp = shader_node.inputs["Metallic"]
        s_out = self.ng_aorm.inputs["metalness"]
        assert isinstance(s_inp, b_t.NodeSocketFloatFactor), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketFloatFactor), type(s_out)
        self._set_up_link(s_inp, s_out, s_inp.default_value)

    def _set_up_emit_color(
        self,
        shader_node: b_t.ShaderNodeBsdfPrincipled,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        s_inp = shader_node.inputs["Base Color"]
        s_out = bake_out_node.inputs["Surface"]
        s_def_inp = self.ng_color.inputs["color"]
        s_def_out = self.ng_color.outputs["color"]
        assert isinstance(s_inp, b_t.NodeSocketColor), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketShader), type(s_out)
        assert isinstance(s_def_inp, b_t.NodeSocketColor), type(s_def_inp)
        assert isinstance(s_def_out, b_t.NodeSocketColor), type(s_def_out)
        self._set_up_link(s_inp, s_out, s_inp.default_value, s_def_inp, s_def_out)

    def _set_up_emit_roughness(
        self,
        shader_node: b_t.ShaderNodeBsdfPrincipled,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        s_inp = shader_node.inputs["Roughness"]
        s_out = bake_out_node.inputs["Surface"]
        s_def_inp = self.ng_aorm.inputs["roughness"]
        s_def_out = self.ng_aorm.outputs["roughness"]
        assert isinstance(s_inp, b_t.NodeSocketFloatFactor), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketShader), type(s_out)
        assert isinstance(s_def_inp, b_t.NodeSocketFloatFactor), type(s_def_inp)
        assert isinstance(s_def_out, b_t.NodeSocketFloatFactor), type(s_def_out)
        self._set_up_link(s_inp, s_out, s_inp.default_value, s_def_inp, s_def_out)

    def _set_up_emit_metalness(
        self,
        shader_node: b_t.ShaderNodeBsdfPrincipled,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        s_inp = shader_node.inputs["Metallic"]
        s_out = bake_out_node.inputs["Surface"]
        s_def_inp = self.ng_aorm.inputs["metalness"]
        s_def_out = self.ng_aorm.outputs["metalness"]
        assert isinstance(s_inp, b_t.NodeSocketFloatFactor), type(s_inp)
        assert isinstance(s_out, b_t.NodeSocketShader), type(s_out)
        assert isinstance(s_def_inp, b_t.NodeSocketFloatFactor), type(s_def_inp)
        assert isinstance(s_def_out, b_t.NodeSocketFloatFactor), type(s_def_out)
        self._set_up_link(s_inp, s_out, s_inp.default_value, s_def_inp, s_def_out)

    def _set_up_opacity(
        self,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        s_out = bake_out_node.inputs["Surface"]
        s_def_inp = self.ng_aorm.inputs["metalness"]
        s_def_out = self.ng_aorm.outputs["metalness"]
        assert isinstance(s_out, b_t.NodeSocketShader), type(s_out)
        assert isinstance(s_def_inp, b_t.NodeSocketFloatFactor), type(s_def_inp)
        assert isinstance(s_def_out, b_t.NodeSocketFloatFactor), type(s_def_out)
        s_def_inp.default_value = 1.0
        self.links.new(s_def_out, s_out)

    def _set_up_mat_id(
        self,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        s_out = bake_out_node.inputs["Surface"]
        if self.bake_settings.matid_use_object_color:
            s_inp = self.ng_color.outputs["object_color"]
        else:
            s_inp = self.ng_color.outputs["color"]
        assert isinstance(s_out, b_t.NodeSocketShader), type(s_out)
        assert isinstance(s_inp, b_t.NodeSocketColor), type(s_inp)

        self.links.new(s_inp, s_out)

    def _set_up_grid(
        self,
        bake_out_node: b_t.ShaderNodeOutputMaterial,
    ) -> None:
        grid_img_name: str
        texture_size = TextureSize(
            width=int(self.bake_settings.size), height=int(self.bake_settings.size)
        )
        _init_uv_maps(texture_size)
        if self.bake_settings.type == BakeTextureType.UTILS_GRID_COLOR.name:
            grid_img_name = _get_color_grid_map_name(texture_size)
        elif self.bake_settings.type == BakeTextureType.UTILS_GRID_UV.name:
            grid_img_name = _get_uv_grid_map_name(texture_size)

        texture_node = self._add_node(
            b_t.ShaderNodeTexImage, MaterialNodeNames.UV_TEXTURE
        )
        assert isinstance(texture_node, b_t.ShaderNodeTexImage)
        # FIXME: map is being deleted from other materials if we have multiple materials
        texture_node.image = bpy.data.images[grid_img_name]

        self.links.new(texture_node.outputs["Color"], bake_out_node.inputs["Surface"])

    def __init__(
        self,
        *,
        mat: b_t.Material,
        bake_settings: BakeSettings,
        image_name: str,
        mat_id_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        """Prepare material for baking."""
        AssetLibraryManager.node_groups_load()

        assert isinstance(mat.node_tree, b_t.ShaderNodeTree), type(mat.node_tree)
        self.tree = mat.node_tree
        self.links = self.tree.links
        self.start_location = Vector((500, 500))  # type: ignore[no-untyped-call]
        self.mat = mat
        self.bake_settings = bake_settings
        self.mat_id_color = mat_id_color

        self.output_node = self.tree.get_output_node("CYCLES")
        # TODO: we shouldn't care about existing material outputs when baking matid?
        if self.tree.get_output_node("CYCLES") is None:
            # TODO: only modify node group once
            # node_groups: list[b_t.ShaderNodeGroup] = []
            # for node in tree.nodes:
            #     if isinstance(node, b_t.ShaderNodeGroup):
            #         node_groups.append(node)

            raise AddonException("Can't bake material without material outputs")

        self.frame = self._get_node_frame()

        self.ng_color = self._add_color_node_group()
        self.ng_aorm = self._add_aorm_node_group()

        bake_texture_node = self._get_node_bake_texture()
        bake_texture_node.image = bpy.data.images.get(image_name)
        if bake_texture_node.image is None:
            log(f"bake_texture_node.image is None for name: {image_name}")
        # TODO: ensure it selected before baking
        # bake_texture_node.select = True
        # tree.nodes.active = bake_texture_node

        if BakeTextureType[bake_settings.type].is_native:
            return

        self._material_setup()

    def _material_setup(self) -> None:
        """Set up utils in the material."""
        bake_out_node = self._get_node_bake_output()
        shader_node = self._get_shader_node()

        if self.bake_settings.type == BakeTextureType.AO.name:
            self._set_up_ao(shader_node, bake_out_node)
        if self.bake_settings.type == BakeTextureType.AORM.name:
            self._set_up_aorm(shader_node, bake_out_node)
        if self.bake_settings.type == BakeTextureType.EMIT_COLOR.name:
            self._set_up_emit_color(shader_node, bake_out_node)
        if self.bake_settings.type == BakeTextureType.EMIT_ROUGHNESS.name:
            self._set_up_emit_roughness(shader_node, bake_out_node)
        if self.bake_settings.type == BakeTextureType.EMIT_METALNESS.name:
            self._set_up_emit_metalness(shader_node, bake_out_node)
        if self.bake_settings.type == BakeTextureType.EMIT_OPACITY.name:
            self._set_up_opacity(bake_out_node)
        if self.bake_settings.type == BakeTextureType.MATERIAL_ID.name:
            self._set_up_mat_id(bake_out_node)
        if self.bake_settings.type in [
            BakeTextureType.UTILS_GRID_COLOR.name,
            BakeTextureType.UTILS_GRID_UV.name,
        ]:
            self._set_up_grid(bake_out_node)


def material_cleanup(mat: b_t.Material) -> None:
    """Cleanup utils in the material."""
    # log(f"Cleaning up material: {self.target_material_name!r}")
    nodes = mat.node_tree.nodes

    nodes_to_remove = []
    for node in nodes:
        if node.name.startswith(NODE_PREFIX):
            nodes_to_remove.append(node)

    # log("Nodes to remove", nodes_to_remove)
    for node in nodes_to_remove:
        nodes.remove(node)

    images_to_remove = []

    # TODO: do not remove if used in other materials?
    for img in bpy.data.images:
        if img.name.startswith(MAP_PREFIX):
            # TODO: Check if it used in other material\node
            images_to_remove.append(img)

    # log("Images to remove", images_to_remove)
    for img in images_to_remove:
        if img is None:
            log("Image is None")
            continue
        # log(f"Trying to remove image {img.name!r}. Users: {img.users!r}")
        bpy.data.images.remove(img)


@Registry.add
class MaterialCleanupSelected(b_t.Operator):
    """Cleanup utils in the selected materials."""

    bl_idname = "pawsbkr.material_cleanup_selected"
    bl_label = "Cleanup Selected Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, _context: b_t.Context) -> set[str]:
        """Operator execute override."""
        selected_mats = tuple(get_selected_materials())
        for mat in selected_mats:
            material_cleanup(mat)

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class MaterialSetupSelected(b_t.Operator):
    """Setup utils in the selected materials."""

    bl_idname = "pawsbkr.material_setup_selected"
    bl_label = "Setup Selected Materials"
    bl_options = {"REGISTER", "UNDO"}

    settings_id: b_p.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def execute(self, context: b_t.Context) -> set[str]:
        """Operator execute override."""
        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")
        cfg = get_bake_settings(context, self.settings_id)

        selected_mats = tuple(get_selected_materials())
        colors = generate_color_set(len(selected_mats))
        for mat in selected_mats:
            material_cleanup(mat)
            BakeMaterialManager(
                mat=mat,
                bake_settings=cfg,
                image_name="",
                mat_id_color=colors[selected_mats.index(mat)],
            )

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class MaterialSetup(b_t.Operator):
    """Setup utils in the material."""

    bl_idname = "pawsbkr.material_setup"
    bl_label = "Setup Material"
    bl_options = {"REGISTER", "UNDO"}

    cleanup: b_p.BoolProperty(  # type: ignore[valid-type]
        default=False,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    target_material_name: b_p.StringProperty(  # type: ignore[valid-type]
        name="Material Name",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    target_image_name: b_p.StringProperty(  # type: ignore[valid-type]
        name="Bake Image Name",
        description="Name of the image to bake textures into",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    mat_id_color: b_p.FloatVectorProperty()  # type: ignore[valid-type]

    settings_id: b_p.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def _cleanup(self, _context: b_t.Context) -> None:
        mat = bpy.data.materials[self.target_material_name]
        material_cleanup(mat)

    def execute(self, context: b_t.Context) -> set[str]:
        """Operator execute override."""
        if self.cleanup:
            self._cleanup(context)
            return {BlenderOperatorReturnType.FINISHED}

        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")
        cfg = get_bake_settings(context, self.settings_id)

        mat = bpy.data.materials[self.target_material_name]
        BakeMaterialManager(
            mat=mat,
            bake_settings=cfg,
            image_name=self.target_image_name,
            mat_id_color=self.mat_id_color,
        )

        return {BlenderOperatorReturnType.FINISHED}
