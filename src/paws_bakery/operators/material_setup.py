"""Setup material utils."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Type, TypeVar

import bpy
from bpy import props as b_p
from bpy import types as b_t
from mathutils import Vector

from .._helpers import UTIL_MATS_PATH, log
from ..enums import BlenderOperatorReturnType
from ..props import BakeSettings, BakeTextureType, get_bake_settings
from ..utils import AddonException, Registry
from ._utils import generate_color_set, get_selected_materials

MAP_PREFIX = "pawsbkr_map_"
NODE_PREFIX = "pawsbkr_utils_"

UTIL_NODES_GROUP_AORM = "pawsbkr_utils_aorm"
UTIL_NODES_GROUP_COLOR = "pawsbkr_utils_color"

UTIL_NODE_GROUPS = [
    UTIL_NODES_GROUP_AORM,
    UTIL_NODES_GROUP_COLOR,
]


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
    OUT = auto()
    UV_TEXTURE = auto()
    VALUE = auto()

    #     def __new__(cls, name):
    #         obj = str.__new__(cls, NODE_PREFIX + name)
    #         obj._value_ = NODE_PREFIX + name
    #
    #         return obj

    def __str__(self) -> str:
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


def _load_node_groups_from_lib() -> None:
    if all(ng_name in bpy.data.node_groups for ng_name in UTIL_NODE_GROUPS):
        return

    log("Some Node Groups are missing. Loading...")

    with bpy.data.libraries.load(str(UTIL_MATS_PATH)) as (data_src, data_dst):
        for ng_name in UTIL_NODE_GROUPS:
            if ng_name not in data_src.node_groups:
                raise AddonException(f"No Node Group with name {ng_name!r} found")
            data_dst.node_groups.append(ng_name)

    for ng_name in UTIL_NODE_GROUPS:
        ng = bpy.data.node_groups.get(ng_name)
        ng.use_fake_user = False

def _setup_position_bake(tree, out_node, frame, start_location):
    """Setup nodes for position baking."""
    # Geometry node for position
    geometry_node = tree.nodes.new('ShaderNodeNewGeometry')
    geometry_node.name = f"{NODE_PREFIX}geometry"
    geometry_node.parent = frame
    geometry_node.location = start_location
    
    # Vector mapping to normalize position
    mapping_node = tree.nodes.new('ShaderNodeMapping')
    mapping_node.name = f"{NODE_PREFIX}mapping"
    mapping_node.parent = frame
    mapping_node.location = (start_location.x + 200, start_location.y)
    
    # Connect geometry position to mapping
    tree.links.new(geometry_node.outputs['Position'], mapping_node.inputs['Vector'])
    tree.links.new(mapping_node.outputs['Vector'], out_node.inputs['Surface'])

def _setup_uv_bake(tree, out_node, frame, start_location):
    """Setup nodes for UV coordinate baking."""
    # UV Map node
    uv_node = tree.nodes.new('ShaderNodeUVMap')
    uv_node.name = f"{NODE_PREFIX}uv_map"
    uv_node.parent = frame
    uv_node.location = start_location
    
    # Separate XYZ to get UV as RGB
    separate_node = tree.nodes.new('ShaderNodeSeparateXYZ')
    separate_node.name = f"{NODE_PREFIX}separate_uv"
    separate_node.parent = frame
    separate_node.location = (start_location.x + 200, start_location.y)
    
    # Combine XYZ to create color output
    combine_node = tree.nodes.new('ShaderNodeCombineXYZ')
    combine_node.name = f"{NODE_PREFIX}combine_uv"
    combine_node.parent = frame
    combine_node.location = (start_location.x + 400, start_location.y)
    
    # Connect UV -> Separate -> Combine -> Output
    tree.links.new(uv_node.outputs['UV'], separate_node.inputs['Vector'])
    tree.links.new(separate_node.outputs['X'], combine_node.inputs['X'])
    tree.links.new(separate_node.outputs['Y'], combine_node.inputs['Y'])
    # Set Z to 0 for UV coordinates
    combine_node.inputs['Z'].default_value = 0.0
    
    tree.links.new(combine_node.outputs['Vector'], out_node.inputs['Surface'])

def _setup_shadow_bake(tree, out_node, frame, start_location):
    """Setup nodes for shadow baking."""
    # Light Path node to detect shadow rays
    light_path_node = tree.nodes.new('ShaderNodeLightPath')
    light_path_node.name = f"{NODE_PREFIX}light_path"
    light_path_node.parent = frame
    light_path_node.location = start_location
    
    # Math node to invert shadow (1.0 - shadow)
    math_node = tree.nodes.new('ShaderNodeMath')
    math_node.name = f"{NODE_PREFIX}shadow_invert"
    math_node.parent = frame
    math_node.location = (start_location.x + 200, start_location.y)
    math_node.operation = 'SUBTRACT'
    math_node.inputs[0].default_value = 1.0
    
    tree.links.new(light_path_node.outputs['Is Shadow Ray'], math_node.inputs[1])
    tree.links.new(math_node.outputs['Value'], out_node.inputs['Surface'])

def _setup_environment_bake(tree, out_node, frame, start_location):
    """Setup nodes for environment baking."""
    # World output - this captures environment lighting
    world_output_node = tree.nodes.new('ShaderNodeOutputWorld')
    world_output_node.name = f"{NODE_PREFIX}world_output"
    world_output_node.parent = frame
    world_output_node.location = start_location
    
    # Background shader for environment
    background_node = tree.nodes.new('ShaderNodeBackground')
    background_node.name = f"{NODE_PREFIX}background"
    background_node.parent = frame
    background_node.location = (start_location.x - 200, start_location.y)
    
    # Environment texture
    env_texture_node = tree.nodes.new('ShaderNodeTexEnvironment')
    env_texture_node.name = f"{NODE_PREFIX}env_texture"
    env_texture_node.parent = frame
    env_texture_node.location = (start_location.x - 400, start_location.y)
    
    tree.links.new(env_texture_node.outputs['Color'], background_node.inputs['Color'])
    tree.links.new(background_node.outputs['Background'], out_node.inputs['Surface'])

def material_setup(
    mat: b_t.Material,
    *,
    bake_settings: BakeSettings,
    image_name: str,
    mat_id_color: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    """Set up utils in the material."""

    _load_node_groups_from_lib()

    tree = mat.node_tree
    links = tree.links

    output_node = tree.get_output_node("CYCLES")

    # TODO: we shouldn't care about existing material outputs when baking matid?
    if output_node is None:
        # TODO: only modify node group once
        # node_groups: list[b_t.ShaderNodeGroup] = []
        # for node in tree.nodes:
        #     if isinstance(node, b_t.ShaderNodeGroup):
        #         node_groups.append(node)

        raise AddonException("Can't bake material without material outputs")

    frame_name = MaterialNodeNames.FRAME
    frame = tree.nodes.get(frame_name)
    if frame is None:
        frame: b_t.NodeFrame = tree.nodes.new(b_t.NodeFrame.__name__)
        frame.name = frame_name
        frame.label = "PAWS: Bakery Utils"
        frame.use_custom_color = True
        frame.color.hsv = (0.25, 0.7, 0.7)

    start_location = Vector((500, 500))

    T = TypeVar("T", bound=b_t.ShaderNode)

    def add_node(node_type: Type[T], name: str) -> T:
        if name in tree.nodes:
            raise AddonException(f"Material already has Node with name {name!r}")
        node: T = tree.nodes.new(node_type.__name__)
        node.name = name
        node.parent = frame
        node.location = start_location
        start_location.y += 250
        return node

    ng_color = add_node(b_t.ShaderNodeGroup, UTIL_NODES_GROUP_COLOR)
    ng_color.node_tree = bpy.data.node_groups.get(UTIL_NODES_GROUP_COLOR)
    ng_color.inputs["color"].default_value = tuple(mat_id_color) + (1.0,)

    ng_aorm = add_node(b_t.ShaderNodeGroup, UTIL_NODES_GROUP_AORM)
    ng_aorm.node_tree = bpy.data.node_groups.get(UTIL_NODES_GROUP_AORM)

    node_name = MaterialNodeNames.BAKE_TEXTURE
    bake_texture_node = tree.nodes.get(node_name)
    if bake_texture_node is None:
        bake_texture_node = tree.nodes.new(b_t.ShaderNodeTexImage.__name__)
        bake_texture_node.name = bake_texture_node.label = node_name
        bake_texture_node.parent = frame
        bake_texture_node.location = (800, 600)

    bake_texture_node.image = bpy.data.images.get(image_name)
    if bake_texture_node.image is None:
        log(f"bake_texture_node.image is None for name: {image_name}")
    # TODO: ensure it selected before baking
    # bake_texture_node.select = True
    # tree.nodes.active = bake_texture_node

    if bake_settings.type not in [
        BakeTextureType.DIFFUSE.name,
        BakeTextureType.EMIT.name,
        BakeTextureType.NORMAL.name,
        BakeTextureType.ROUGHNESS.name,
    ]:
        node_name = MaterialNodeNames.OUT
        out_node = tree.nodes.get(node_name)
        if out_node is None:
            out_node = tree.nodes.new(b_t.ShaderNodeOutputMaterial.__name__)
            out_node.name = out_node.label = node_name
            out_node.parent = frame
            out_node.location = (800, 800)

            tree.nodes.active = out_node

    # TEXTURE BAKING

    # TODO: filter muted and not connected out nodes
    output_nodes = []
    for node in tree.nodes:
        if (
            node.name == MaterialNodeNames.OUT
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

    from_node = output_nodes[0].inputs["Surface"].links[0].from_node

    # TODO: add more shader types?
    if not isinstance(from_node, b_t.ShaderNodeBsdfPrincipled):
        raise AddonException("Can't bake material with current shader type")

    if bake_settings.type == BakeTextureType.AO.name:
        links.new(ng_aorm.outputs["ao"], out_node.inputs["Surface"])

        target_input = from_node.inputs["Normal"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, ng_aorm.inputs["normal"])

    if bake_settings.type == BakeTextureType.AORM.name:
        links.new(ng_aorm.outputs["aorm"], out_node.inputs["Surface"])

        target_input = from_node.inputs["Normal"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, ng_aorm.inputs["normal"])

        target_input = from_node.inputs["Roughness"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, ng_aorm.inputs["roughness"])
        else:
            ng_aorm.inputs["roughness"].default_value = target_input.default_value

        target_input = from_node.inputs["Metallic"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, ng_aorm.inputs["metalness"])
        else:
            ng_aorm.inputs["metalness"].default_value = target_input.default_value

    if bake_settings.type == BakeTextureType.EMIT_COLOR.name:
        target_input = from_node.inputs["Base Color"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, out_node.inputs["Surface"])
        else:
            ng_color.inputs["color"].default_value = target_input.default_value
            links.new(ng_color.outputs["color"], out_node.inputs["Surface"])

    if bake_settings.type == BakeTextureType.EMIT_ROUGHNESS.name:
        target_input = from_node.inputs["Roughness"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, out_node.inputs["Surface"])
        else:
            ng_aorm.outputs["roughness"].default_value = target_input.default_value
            links.new(ng_aorm.outputs["roughness"], out_node.inputs["Surface"])

    if bake_settings.type == BakeTextureType.EMIT_METALNESS.name:
        target_input = from_node.inputs["Metallic"]
        if target_input.is_linked:
            target_socket = target_input.links[0].from_socket
            links.new(target_socket, out_node.inputs["Surface"])
        else:

            ng_aorm.outputs["metalness"].default_value = target_input.default_value
            links.new(ng_aorm.outputs["metalness"], out_node.inputs["Surface"])

    if bake_settings.type == BakeTextureType.EMIT_OPACITY.name:
        ng_aorm.outputs["metalness"].default_value = 1.0
        links.new(ng_aorm.outputs["metalness"], out_node.inputs["Surface"])

    if bake_settings.type == BakeTextureType.MATERIAL_ID.name:
        if bake_settings.matid_use_object_color:
            links.new(ng_color.outputs["object_color"], out_node.inputs["Surface"])
        else:
            links.new(ng_color.outputs["color"], out_node.inputs["Surface"])

    if bake_settings.type == BakeTextureType.POSITION.name:
        _setup_position_bake(tree, out_node, frame, start_location)
    
    if bake_settings.type == BakeTextureType.UV.name:
        _setup_uv_bake(tree, out_node, frame, start_location)
    
    if bake_settings.type == BakeTextureType.SHADOW.name:
        _setup_shadow_bake(tree, out_node, frame, start_location)
    
    if bake_settings.type == BakeTextureType.ENVIRONMENT.name:
        _setup_environment_bake(tree, out_node, frame, start_location)
    
    if bake_settings.type == BakeTextureType.GLOSSY.name:
        # For glossy, we use the material's existing glossy component
        if isinstance(from_node, b_t.ShaderNodeBsdfPrincipled):
            # Create a glossy BSDF node
            glossy_node = tree.nodes.new('ShaderNodeBsdfGlossy')
            glossy_node.name = f"{NODE_PREFIX}glossy_bsdf"
            glossy_node.parent = frame
            glossy_node.location = start_location
            
            # Copy roughness from principled BSDF
            target_input = from_node.inputs["Roughness"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, glossy_node.inputs["Roughness"])
            else:
                glossy_node.inputs["Roughness"].default_value = target_input.default_value
            
            links.new(glossy_node.outputs["BSDF"], out_node.inputs["Surface"])
    
    if bake_settings.type == BakeTextureType.TRANSMISSION.name:
        # For transmission baking
        if isinstance(from_node, b_t.ShaderNodeBsdfPrincipled):
            # Use transmission component of principled BSDF
            target_input = from_node.inputs.get("Transmission")
            if target_input:
                if target_input.is_linked:
                    target_socket = target_input.links[0].from_socket
                    links.new(target_socket, out_node.inputs["Surface"])
                else:
                    # Create emission node with transmission value
                    emission_node = tree.nodes.new('ShaderNodeEmission')
                    emission_node.name = f"{NODE_PREFIX}transmission_emit"
                    emission_node.parent = frame
                    emission_node.location = start_location
                    emission_node.inputs["Color"].default_value = (
                        target_input.default_value,
                        target_input.default_value, 
                        target_input.default_value,
                        1.0
                    )
                    links.new(emission_node.outputs["Emission"], out_node.inputs["Surface"])

    if bake_settings.type in [
        BakeTextureType.UTILS_GRID_COLOR.name,
        BakeTextureType.UTILS_GRID_UV.name,
    ]:
        grid_img_name: str
        texture_size = TextureSize(
            width=int(bake_settings.size), height=int(bake_settings.size)
        )
        _init_uv_maps(texture_size)
        if bake_settings.type == BakeTextureType.UTILS_GRID_COLOR.name:
            grid_img_name = _get_color_grid_map_name(texture_size)
        elif bake_settings.type == BakeTextureType.UTILS_GRID_UV.name:
            grid_img_name = _get_uv_grid_map_name(texture_size)

        texture_node = add_node(b_t.ShaderNodeTexImage, MaterialNodeNames.UV_TEXTURE)
        # FIXME: map is being deleted from other materials if we have multiple materials
        texture_node.image = bpy.data.images[grid_img_name]

        links.new(texture_node.outputs["Color"], out_node.inputs["Surface"])


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
        """execute() override."""
        selected_mats = get_selected_materials()
        for mat in selected_mats.values():
            material_cleanup(mat)

        return {BlenderOperatorReturnType.FINISHED}


@Registry.add
class MaterialSetupSelected(b_t.Operator):
    """Setup utils in the selected materials."""

    bl_idname = "pawsbkr.material_setup_selected"
    bl_label = "Setup Selected Materials"
    bl_options = {"REGISTER", "UNDO"}

    settings_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")
        cfg = get_bake_settings(context, self.settings_id)

        selected_mats = get_selected_materials()
        colors = generate_color_set(len(selected_mats))
        for mat in selected_mats.values():
            material_cleanup(mat)
        for mat in selected_mats.values():
            material_setup(
                mat,
                bake_settings=cfg,
                image_name="",
                mat_id_color=colors[list(selected_mats.values()).index(mat)],
            )

        return {BlenderOperatorReturnType.FINISHED}


# TODO: Move to and load most of the nodes setup from the .blend file
@Registry.add
class MaterialSetup(b_t.Operator):
    """Setup utils in the material."""

    bl_idname = "pawsbkr.material_setup"
    bl_label = "Setup Material"
    bl_options = {"REGISTER", "UNDO"}

    cleanup: b_p.BoolProperty(
        default=False,
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    target_material_name: b_p.StringProperty(
        name="Material Name",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    target_image_name: b_p.StringProperty(
        name="Bake Image Name",
        description="Name of the image to bake textures into",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    mat_id_color: b_p.FloatVectorProperty()

    settings_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def _cleanup(self, _context: b_t.Context) -> None:
        mat = bpy.data.materials[self.target_material_name]
        material_cleanup(mat)

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        # log(f"Cleanup: {self.cleanup!r}. texture_type: {self.texture_type!r}")
        if self.cleanup:
            self._cleanup(context)
            return {BlenderOperatorReturnType.FINISHED}

        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")
        cfg = get_bake_settings(context, self.settings_id)

        mat = bpy.data.materials[self.target_material_name]
        material_setup(
            mat,
            bake_settings=cfg,
            image_name=self.target_image_name,
            mat_id_color=self.mat_id_color,
        )

        return {BlenderOperatorReturnType.FINISHED}
