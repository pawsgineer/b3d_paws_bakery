"""Setup material utils."""

from enum import Enum, auto

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderOperatorReturnType
from ..props import BakeTextureType
from ..utils import AddonException, Registry
from ._utils import generate_color_set, get_selected_materials

MAP_PREFIX = "pawsbkr_map_"
NODE_PREFIX = "pawsbkr_utils_"


class MaterialNodeNames(str, Enum):
    """Managed material node names."""

    # pylint: disable-next=no-self-argument
    def _generate_next_value_(  # type: ignore[no-untyped-def]
        name, _start, _count, _last_values  # noqa: B902
    ):
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
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)

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
        cfg = context.scene.pawsbkr.get_bake_settings(self.settings_id)

        selected_mats = get_selected_materials()
        colors = generate_color_set(len(selected_mats))
        for mat in selected_mats.values():
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)
            bpy.ops.pawsbkr.material_setup(
                target_material_name=mat.name,
                cleanup=False,
                mat_id_color=colors[list(selected_mats.values()).index(mat)],
                texture_type=cfg.type,
                texture_width=int(cfg.size),
                texture_height=int(cfg.size),
                settings_id=self.settings_id,
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
    texture_type: BakeTextureType.get_blender_enum_property()
    texture_width: b_p.IntProperty()
    texture_height: b_p.IntProperty()

    settings_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    def _get_uv_grid_map_name(self) -> str:
        uv_size = f"{self.texture_width}_{self.texture_height}"
        return f"{MAP_PREFIX}uv_{uv_size}"

    def _get_color_grid_map_name(self) -> str:
        uv_size = f"{self.texture_width}_{self.texture_height}"
        return f"{MAP_PREFIX}color_{uv_size}"

    def _init_uv_maps(self) -> None:
        "Create uv map images."
        if bpy.data.images.get(self._get_uv_grid_map_name()) is None:
            bpy.ops.image.new(
                name=self._get_uv_grid_map_name(),
                width=self.texture_width,
                height=self.texture_height,
                generated_type="UV_GRID",
            )
        if bpy.data.images.get(self._get_color_grid_map_name()) is None:
            bpy.ops.image.new(
                name=self._get_color_grid_map_name(),
                width=self.texture_width,
                height=self.texture_height,
                generated_type="COLOR_GRID",
            )

    def _cleanup(self, _context: b_t.Context):
        # log(f"Cleaning up material: {self.target_material_name!r}")

        mat = bpy.data.materials[self.target_material_name]
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

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        # log(f"Cleanup: {self.cleanup!r}. texture_type: {self.texture_type!r}")
        if self.cleanup:
            self._cleanup(context)
            return {BlenderOperatorReturnType.FINISHED}

        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")
        cfg = context.scene.pawsbkr.get_bake_settings(self.settings_id)

        mat = bpy.data.materials[self.target_material_name]
        tree = mat.node_tree
        links = tree.links

        frame_name = MaterialNodeNames.FRAME
        frame = tree.nodes.get(frame_name)
        if frame is None:
            frame = tree.nodes.new("NodeFrame")
            frame.name = frame_name
            frame.label = "PAWS Bakery Utils"
            frame.use_custom_color = True
            frame.color.hsv = (0.25, 0.7, 0.7)

        node_name = MaterialNodeNames.BAKE_TEXTURE
        bake_texture_node = tree.nodes.get(node_name)
        if bake_texture_node is None:
            bake_texture_node = tree.nodes.new(b_t.ShaderNodeTexImage.__name__)
            bake_texture_node.name = bake_texture_node.label = node_name
            bake_texture_node.parent = frame
            bake_texture_node.location = (360, 1380)

        bake_texture_node.image = bpy.data.images.get(self.target_image_name)
        if bake_texture_node.image is None:
            log(f"bake_texture_node.image is None for name: {self.target_image_name}")
        # TODO: ensure it selected before baking
        # bake_texture_node.select = True
        # tree.nodes.active = bake_texture_node

        if self.texture_type not in [
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
                out_node.location = (360, 1500)

                tree.nodes.active = out_node

        node_name = MaterialNodeNames.AO
        ao_node = tree.nodes.get(node_name)
        if ao_node is None:
            ao_node = tree.nodes.new(b_t.ShaderNodeAmbientOcclusion.__name__)
            ao_node.name = ao_node.label = node_name
            ao_node.parent = frame
            ao_node.location = (-160, 920)

            # TODO: PARAMETRIZE
            ao_node.samples = 32
            ao_node.only_local = True

        node_name = MaterialNodeNames.OBJECT_INFO
        object_info_node = tree.nodes.get(node_name)
        if object_info_node is None:
            object_info_node = tree.nodes.new(b_t.ShaderNodeObjectInfo.__name__)
            object_info_node.name = object_info_node.label = node_name
            object_info_node.parent = frame
            object_info_node.location = (-160, 1240)

        node_name = MaterialNodeNames.COLOR
        color_node = tree.nodes.get(node_name)
        if color_node is None:
            color_node = tree.nodes.new(b_t.ShaderNodeBrightContrast.__name__)
            color_node.name = color_node.label = node_name
            color_node.parent = frame
            color_node.location = (-160, 1060)

            color_node.inputs["Color"].default_value = tuple(self.mat_id_color) + (1.0,)

        node_name = MaterialNodeNames.COMBINE_COLOR
        combine_color_node = tree.nodes.get(node_name)
        if combine_color_node is None:
            combine_color_node = tree.nodes.new(b_t.ShaderNodeCombineColor.__name__)
            combine_color_node.name = combine_color_node.label = node_name
            combine_color_node.parent = frame
            combine_color_node.location = (20, 920)

        node_name = MaterialNodeNames.VALUE + "_roughness"
        roughness_value_node = tree.nodes.get(node_name)
        if roughness_value_node is None:
            roughness_value_node = tree.nodes.new(b_t.ShaderNodeValue.__name__)
            roughness_value_node.name = roughness_value_node.label = node_name
            roughness_value_node.parent = frame
            roughness_value_node.location = (-160, 700)

        node_name = MaterialNodeNames.VALUE + "_metalness"
        metalness_value_node = tree.nodes.get(node_name)
        if metalness_value_node is None:
            metalness_value_node = tree.nodes.new(b_t.ShaderNodeValue.__name__)
            metalness_value_node.name = metalness_value_node.label = node_name
            metalness_value_node.parent = frame
            metalness_value_node.location = (-160, 620)

        # TEXTURE BAKING

        # TODO: filter muted and not connected out nodes
        output_nodes = []
        for node in tree.nodes:
            if (
                isinstance(node, b_t.ShaderNodeOutputMaterial)
                and node.name != MaterialNodeNames.OUT
            ):
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

        if self.texture_type == BakeTextureType.AO.name:
            links.new(ao_node.outputs["Color"], out_node.inputs["Surface"])

            target_input = from_node.inputs["Normal"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, ao_node.inputs["Normal"])

        if self.texture_type == BakeTextureType.AORM.name:
            links.new(combine_color_node.outputs["Color"], out_node.inputs["Surface"])

            links.new(ao_node.outputs["Color"], combine_color_node.inputs["Red"])

            target_input = from_node.inputs["Normal"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, ao_node.inputs["Normal"])

            target_input = from_node.inputs["Roughness"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, combine_color_node.inputs["Green"])
            else:
                roughness_value_node.outputs["Value"].default_value = (
                    target_input.default_value
                )
                links.new(
                    roughness_value_node.outputs["Value"],
                    combine_color_node.inputs["Green"],
                )

            target_input = from_node.inputs["Metallic"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, combine_color_node.inputs["Blue"])
            else:

                metalness_value_node.outputs["Value"].default_value = (
                    target_input.default_value
                )
                links.new(
                    metalness_value_node.outputs["Value"],
                    combine_color_node.inputs["Blue"],
                )

        if self.texture_type == BakeTextureType.EMIT_COLOR.name:
            target_input = from_node.inputs["Base Color"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, out_node.inputs["Surface"])
            else:
                color_node.inputs["Color"].default_value = target_input.default_value
                links.new(color_node.outputs["Color"], out_node.inputs["Surface"])

        if self.texture_type == BakeTextureType.EMIT_ROUGHNESS.name:
            target_input = from_node.inputs["Roughness"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, out_node.inputs["Surface"])
            else:
                roughness_value_node.outputs["Value"].default_value = (
                    target_input.default_value
                )
                links.new(
                    roughness_value_node.outputs["Value"], out_node.inputs["Surface"]
                )

        if self.texture_type == BakeTextureType.EMIT_METALNESS.name:
            target_input = from_node.inputs["Metallic"]
            if target_input.is_linked:
                target_socket = target_input.links[0].from_socket
                links.new(target_socket, out_node.inputs["Surface"])
            else:

                metalness_value_node.outputs["Value"].default_value = (
                    target_input.default_value
                )
                links.new(
                    metalness_value_node.outputs["Value"], out_node.inputs["Surface"]
                )

        if self.texture_type == BakeTextureType.EMIT_OPACITY.name:
            metalness_value_node.outputs["Value"].default_value = 1.0
            links.new(metalness_value_node.outputs["Value"], out_node.inputs["Surface"])

        if self.texture_type == BakeTextureType.MATERIAL_ID.name:
            if cfg.matid_use_object_color:
                links.new(object_info_node.outputs["Color"], out_node.inputs["Surface"])
            else:
                links.new(color_node.outputs["Color"], out_node.inputs["Surface"])

        if self.texture_type in [
            BakeTextureType.UTILS_GRID_COLOR.name,
            BakeTextureType.UTILS_GRID_UV.name,
        ]:
            self._init_uv_maps()
            if self.texture_type == BakeTextureType.UTILS_GRID_COLOR.name:
                grid_img_name = self._get_color_grid_map_name()
            elif self.texture_type == BakeTextureType.UTILS_GRID_UV.name:
                grid_img_name = self._get_uv_grid_map_name()

            node_name = MaterialNodeNames.UV_TEXTURE
            texture_node = tree.nodes.get(node_name)
            if texture_node is None:
                texture_node = tree.nodes.new(b_t.ShaderNodeTexImage.__name__)
                texture_node.name = texture_node.label = node_name
                texture_node.parent = frame
                texture_node.location = (-270, 1500)

            texture_node.image = bpy.data.images[grid_img_name]

            links.new(texture_node.outputs["Color"], out_node.inputs["Surface"])

        return {BlenderOperatorReturnType.FINISHED}
