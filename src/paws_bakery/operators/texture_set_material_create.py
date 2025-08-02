"""Texture Set Material Creator - DEBUG VERSION - Creates materials from baked textures."""

import bpy
from bpy import props as b_p
from bpy import types as b_t
from pathlib import Path
from typing import Dict, List, Set, Optional

from .._helpers import UTIL_MATS_PATH, log
from ..enums import BlenderOperatorReturnType
from ..props import get_bake_settings, get_props
from ..props_enums import BakeTextureType, TextureTypeAlias
from ..utils import AddonException, Registry

# Template material names in materials.blend
TEMPLATE_MATERIALS = {
    "basic": "pawsbkr_material_basic",
    "pbr_full": "pawsbkr_material_pbr_full",
    "user_custom": "pawsbkr_material_custom_user",
}


def _map_bake_type_to_texture_alias(bake_type: str) -> Optional[TextureTypeAlias]:
    """Map BakeTextureType to TextureTypeAlias for node naming."""
    mapping = {
        BakeTextureType.DIFFUSE.name: TextureTypeAlias.ALBEDO,
        BakeTextureType.COMBINED.name: TextureTypeAlias.ALBEDO,
        BakeTextureType.EMIT_COLOR.name: TextureTypeAlias.ALBEDO,
        BakeTextureType.MATERIAL_ID.name: TextureTypeAlias.ALBEDO,
        BakeTextureType.NORMAL.name: TextureTypeAlias.NORMAL,
        BakeTextureType.ROUGHNESS.name: TextureTypeAlias.ROUGHNESS,
        BakeTextureType.EMIT_ROUGHNESS.name: TextureTypeAlias.ROUGHNESS,
        BakeTextureType.EMIT.name: TextureTypeAlias.EMISSION,
        BakeTextureType.EMIT_METALNESS.name: TextureTypeAlias.METALNESS,
        BakeTextureType.EMIT_OPACITY.name: TextureTypeAlias.OPACITY,
        BakeTextureType.AO.name: TextureTypeAlias.AMBIENT_OCCLUSION,
        BakeTextureType.SHADOW.name: TextureTypeAlias.AMBIENT_OCCLUSION,  # Shadow uses AO nodes
        BakeTextureType.AORM.name: TextureTypeAlias.AORM,
        # These don't have direct node equivalents
        BakeTextureType.POSITION.name: None,
        BakeTextureType.UV.name: None,
        BakeTextureType.ENVIRONMENT.name: None,
        BakeTextureType.UTILS_GRID_COLOR.name: None,
        BakeTextureType.UTILS_GRID_UV.name: None,
    }

    return mapping.get(bake_type)


def _select_base_template(bake_types: Set[str], user_preference: str = "") -> str:
    """Select appropriate base material template based on baked texture types."""
    log(f"Selecting base template for bake types: {bake_types}")

    # User override
    if user_preference and user_preference in TEMPLATE_MATERIALS.values():
        log(f"Using user preference: {user_preference}")
        return user_preference

    # Auto-selection logic
    complex_types = {
        BakeTextureType.AO.name,
        BakeTextureType.EMIT.name,
        BakeTextureType.AORM.name,
        BakeTextureType.SHADOW.name,
    }

    if any(btype in complex_types for btype in bake_types):
        log("Using PBR full template for complex bake types")
        return TEMPLATE_MATERIALS["pbr_full"]
    elif len(bake_types) <= 3:
        log("Using basic template for simple bake types")
        return TEMPLATE_MATERIALS["basic"]
    else:
        log("Using PBR full template for many bake types")
        return TEMPLATE_MATERIALS["pbr_full"]


def _load_material_template(template_name: str) -> b_t.Material:
    """Load material template from materials.blend."""
    log(f"Loading material template: {template_name}")

    if template_name in bpy.data.materials:
        log(f"Template {template_name} already exists in scene, using existing")
        return bpy.data.materials[template_name].copy()

    # Load from materials.blend
    try:
        with bpy.data.libraries.load(
            str(UTIL_MATS_PATH), link=False, assets_only=True
        ) as (data_src, data_dst):
            if template_name not in data_src.materials:
                raise AddonException(
                    f"Template material '{template_name}' not found in materials.blend"
                )
            data_dst.materials = [template_name]

        template_material = bpy.data.materials[template_name]
        log(f"Successfully loaded template: {template_name}")
        return template_material.copy()

    except Exception as e:
        log(f"Failed to load template {template_name}: {e}")
        raise AddonException(
            f"Failed to load material template '{template_name}': {str(e)}"
        )


def _find_texture_nodes_by_prefix(
    material: b_t.Material, tex_alias: TextureTypeAlias
) -> List[b_t.ShaderNodeTexImage]:
    """Find all texture nodes matching the TextureTypeAlias prefix."""
    if not material.node_tree:
        return []

    prefix = tex_alias.node_name
    matching_nodes = []

    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.name.startswith(prefix):
            matching_nodes.append(node)

    log(
        f"Found {len(matching_nodes)} nodes with prefix '{prefix}': {[n.name for n in matching_nodes]}"
    )
    return matching_nodes


def _ensure_texture_node_exists(
    material: b_t.Material, tex_alias: TextureTypeAlias
) -> List[b_t.ShaderNodeTexImage]:
    """Ensure at least one texture node exists for the given texture type."""
    existing_nodes = _find_texture_nodes_by_prefix(material, tex_alias)

    if existing_nodes:
        return existing_nodes

    # Create new texture node
    log(f"Creating new texture node for {tex_alias.node_name}")
    node_tree = material.node_tree
    tex_node = node_tree.nodes.new(type="ShaderNodeTexImage")
    tex_node.name = tex_alias.node_name
    tex_node.label = tex_alias.node_name.replace("_", " ").title()

    # Position node (basic left-side positioning)
    tex_node.location = (-600, len(node_tree.nodes) * -200)

    return [tex_node]


def _cleanup_unused_texture_nodes(
    material: b_t.Material, used_texture_aliases: Set[TextureTypeAlias]
):
    """Remove texture nodes that won't be used by any baked textures."""
    if not material.node_tree:
        return

    used_prefixes = {alias.node_name for alias in used_texture_aliases}
    nodes_to_remove = []

    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            # Check if this node matches any used prefix
            is_used = any(node.name.startswith(prefix) for prefix in used_prefixes)
            if not is_used:
                nodes_to_remove.append(node)

    log(
        f"Removing {len(nodes_to_remove)} unused texture nodes: {[n.name for n in nodes_to_remove]}"
    )
    for node in nodes_to_remove:
        material.node_tree.nodes.remove(node)


def _assign_textures_to_nodes(
    material: b_t.Material, texture_images: Dict[str, b_t.Image]
):
    """Assign baked images to appropriate texture nodes using TextureImport logic."""
    log(f"Assigning {len(texture_images)} textures to material {material.name}")

    for bake_type, image in texture_images.items():
        tex_alias = _map_bake_type_to_texture_alias(bake_type)
        if not tex_alias:
            log(f"No texture alias mapping for bake type: {bake_type}")
            continue

        # Find matching nodes
        texture_nodes = _find_texture_nodes_by_prefix(material, tex_alias)
        if not texture_nodes:
            log(
                f"No texture nodes found for {tex_alias.node_name}, skipping {bake_type}"
            )
            continue

        # Set colorspace
        if tex_alias not in [TextureTypeAlias.ALBEDO, TextureTypeAlias.EMISSION]:
            image.colorspace_settings.name = "Non-Color"

        # Assign image to all matching nodes
        for node in texture_nodes:
            node.image = image
            node.mute = False
            log(f"Assigned {image.name} to node {node.name}")


def _create_material_from_template(
    original_material: b_t.Material,
    texture_set_name: str,
    texture_images: Dict[str, b_t.Image],
    base_template: str = "",
    name_prefix: str = "",
    name_suffix: str = "_baked",
    force_recreate: bool = False,
) -> b_t.Material:
    """Create a new material from template or update existing material with baked textures."""

    # Generate expected material name
    base_name = original_material.name
    expected_name = f"{name_prefix}{base_name}{name_suffix}"

    # Check if material already exists
    existing_material = bpy.data.materials.get(expected_name)

    if existing_material and not force_recreate:
        log(f"Material {expected_name} already exists, updating textures")
        _assign_textures_to_nodes(existing_material, texture_images)
        return existing_material

    # Need to create new material (or recreate existing)
    if existing_material and force_recreate:
        log(f"Recreating existing material: {expected_name}")
        bpy.data.materials.remove(existing_material)

    # Generate unique name if needed
    final_name = expected_name
    counter = 1
    while final_name in bpy.data.materials:
        final_name = f"{expected_name}_{counter:03d}"
        counter += 1

    log(f"Creating material: {final_name}")

    try:
        # Determine which texture types we're working with
        used_bake_types = set(texture_images.keys())

        # Select and load base template
        template_name = base_template or _select_base_template(used_bake_types)
        new_material = _load_material_template(template_name)
        new_material.name = final_name

        # Assign baked textures to nodes
        _assign_textures_to_nodes(new_material, texture_images)

        log(f"Successfully created material: {final_name}")
        return new_material

    except Exception as e:
        log(f"Failed to create material: {e}")
        # Clean up any partially created material
        if "new_material" in locals() and new_material:
            try:
                bpy.data.materials.remove(new_material)
            except:
                pass
        raise AddonException(f"Failed to create material from template: {str(e)}")


@Registry.add
class TextureSetMaterialCreate(b_t.Operator):
    """Create materials from baked textures using templates."""

    bl_idname = "pawsbkr.texture_set_material_create"
    bl_label = "Create Materials from Baked Textures"
    bl_options = {"REGISTER", "UNDO"}

    texture_set_id: b_p.StringProperty(
        name="Target texture set name", default="", options={"HIDDEN", "SKIP_SAVE"}
    )

    assign_to_objects: b_p.BoolProperty(
        name="Assign to Objects",
        description="Assign the new materials to objects in the texture set",
        default=True,
    )

    base_template: b_p.EnumProperty(
        name="Base Template",
        description="Base material template to use",
        items=[
            ("", "Auto Select", "Automatically select template based on bake types"),
            (TEMPLATE_MATERIALS["basic"], "Basic", "Minimal PBR setup"),
            (
                TEMPLATE_MATERIALS["pbr_full"],
                "PBR Full",
                "Complete PBR with all features",
            ),
            (
                TEMPLATE_MATERIALS["user_custom"],
                "User Custom",
                "User customized template",
            ),
        ],
        default=TEMPLATE_MATERIALS["basic"],  # Changed from "" to basic template
    )

    force_recreate: b_p.BoolProperty(
        name="Force Recreate",
        description="Force recreation of materials even if they already exist",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def execute(self, context: b_t.Context) -> set[str]:
        """Execute material creation."""
        log(
            f"TextureSetMaterialCreate.execute() - texture_set_id: {self.texture_set_id}"
        )

        if not self.texture_set_id:
            raise AddonException("texture_set_id is required")

        pawsbkr = get_props(context)
        utils_settings = pawsbkr.utils_settings
        texture_set = pawsbkr.texture_sets[self.texture_set_id]

        # Get global settings
        name_prefix = utils_settings.material_name_prefix
        name_suffix = utils_settings.material_output_suffix

        log(f"Processing texture set: {texture_set.display_name}")

        # Collect baked images
        texture_images: Dict[str, b_t.Image] = {}
        images_found = []
        images_missing = []

        for texture_props in texture_set.textures:
            if not texture_props.is_enabled:
                continue

            bake_settings = get_bake_settings(context, texture_props.prop_id)

            from .bake_common import generate_image_name_and_path

            img_name, img_path = generate_image_name_and_path(
                context=context,
                settings_id=texture_props.prop_id,
                texture_set_name=texture_set.display_name,
            )

            image = bpy.data.images.get(img_name)
            if image:
                texture_images[bake_settings.type] = image
                images_found.append(f"{bake_settings.type}: {img_name}")
            else:
                images_missing.append(f"{bake_settings.type}: {img_name}")

        if not texture_images:
            raise AddonException("No baked images found. Bake textures first.")

        if images_missing:
            self.report({"WARNING"}, f"Missing images: {', '.join(images_missing)}")

        # Get materials from objects in texture set
        materials_to_process: Set[b_t.Material] = set()
        objects_materials: Dict[str, List[b_t.Material]] = {}

        for mesh_props in texture_set.meshes:
            if not mesh_props.is_enabled:
                continue

            obj = mesh_props.get_ref()
            if not obj or obj.type != "MESH":
                continue

            obj_materials = []
            for slot in obj.material_slots:
                if slot.material:
                    materials_to_process.add(slot.material)
                    obj_materials.append(slot.material)

            if obj_materials:
                objects_materials[obj.name] = obj_materials

        if not materials_to_process:
            raise AddonException("No materials found on objects in texture set")

        # Create new materials and assign to objects
        new_materials: Dict[str, b_t.Material] = {}

        for original_mat in materials_to_process:
            log(f"Processing material: {original_mat.name}")

            # Check if material with this name already exists
            expected_name = f"{name_prefix}{original_mat.name}{name_suffix}"
            existing_material = bpy.data.materials.get(expected_name)

            if existing_material:
                log(f"Material {expected_name} already exists, updating textures")
                _assign_textures_to_nodes(existing_material, texture_images)
                new_materials[original_mat.name] = existing_material
            else:
                # Create new material
                new_material = _create_material_from_template(
                    original_material=original_mat,
                    texture_set_name=texture_set.display_name,
                    texture_images=texture_images,
                    base_template=self.base_template,
                    name_prefix=name_prefix,
                    name_suffix=name_suffix,
                    force_recreate=self.force_recreate,
                )
                new_materials[original_mat.name] = new_material

        # Assign materials to objects if requested
        if self.assign_to_objects:
            for obj_name, obj_materials in objects_materials.items():
                obj = bpy.data.objects.get(obj_name)
                if not obj:
                    continue

                for i, slot in enumerate(obj.material_slots):
                    if slot.material and slot.material.name in new_materials:
                        slot.material = new_materials[slot.material.name]
                        log(f"Assigned {slot.material.name} to {obj.name} slot {i}")

        success_msg = f"Created/updated {len(new_materials)} materials with {len(texture_images)} textures"
        log(success_msg)
        self.report({"INFO"}, success_msg)
        return {BlenderOperatorReturnType.FINISHED}

    # def invoke(self, context: b_t.Context, event: b_t.Event) -> set[str]:
    #     """Show dialog for user options."""
    #     return context.window_manager.invoke_props_dialog(self)
