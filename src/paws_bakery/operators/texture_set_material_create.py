"""Texture Set Material Creator - Creates materials from baked textures."""

import bpy
from bpy import props as b_p
from bpy import types as b_t

from ..enums import BlenderOperatorReturnType
from ..props import get_bake_settings, get_props
from ..props_enums import BakeTextureType
from ..utils import AddonException, Registry


def _get_texture_type_socket(material: b_t.Material, texture_type: str) -> str | None:
    """Get the appropriate material socket name for a texture type."""
    # Map texture types to BSDF socket names
    socket_map = {
        BakeTextureType.DIFFUSE.name: "Base Color",
        BakeTextureType.GLOSSY.name: "Base Color", 
        BakeTextureType.NORMAL.name: "Normal",
        BakeTextureType.ROUGHNESS.name: "Roughness",
        BakeTextureType.EMIT.name: "Emission",
        BakeTextureType.AO.name: "Base Color",  # Usually mixed with base color
        BakeTextureType.SHADOW.name: "Base Color",
        BakeTextureType.POSITION.name: None,  # Usually not directly connected
        BakeTextureType.UV.name: None,
        BakeTextureType.ENVIRONMENT.name: "Base Color",
        BakeTextureType.COMBINED.name: "Base Color",
    }
    
    return socket_map.get(texture_type)


def _find_principled_bsdf(material: b_t.Material) -> b_t.ShaderNodeBsdfPrincipled | None:
    """Find the Principled BSDF node in material."""
    if not material.node_tree:
        return None
    
    for node in material.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    return None


def _create_material_from_textures(
    original_material: b_t.Material,
    texture_set_name: str,
    texture_images: dict[str, b_t.Image],
    keep_original: bool = True
) -> b_t.Material:
    """Create a new material with baked textures connected."""
    
    # Create new material name
    suffix = "_baked"
    new_name = f"{original_material.name}{suffix}"
    
    # Ensure unique name
    counter = 1
    while new_name in bpy.data.materials:
        new_name = f"{original_material.name}{suffix}_{counter:03d}"
        counter += 1
    
    if keep_original:
        # Copy the original material
        new_material = original_material.copy()
        new_material.name = new_name
    else:
        # Create a basic material
        new_material = bpy.data.materials.new(name=new_name)
        new_material.use_nodes = True
        
        # Clear default nodes if creating from scratch
        if not keep_original:
            new_material.node_tree.nodes.clear()
            
            # Add basic nodes
            bsdf = new_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
            output = new_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
            
            # Position nodes
            bsdf.location = (0, 0)
            output.location = (300, 0)
            
            # Connect BSDF to output
            new_material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Find the Principled BSDF node
    principled_bsdf = _find_principled_bsdf(new_material)
    if not principled_bsdf:
        raise AddonException(f"Could not find Principled BSDF in material {new_material.name}")
    
    node_tree = new_material.node_tree
    
    # Connect texture images to appropriate sockets
    for texture_type, image in texture_images.items():
        socket_name = _get_texture_type_socket(new_material, texture_type)
        if not socket_name or socket_name not in principled_bsdf.inputs:
            continue
            
        # Create texture node
        tex_node = node_tree.nodes.new(type='ShaderNodeTexImage')
        tex_node.image = image
        tex_node.location = (-400, len(node_tree.nodes) * -200)
        
        # Special handling for normal maps
        if texture_type == BakeTextureType.NORMAL.name:
            # Add normal map node
            normal_node = node_tree.nodes.new(type='ShaderNodeNormalMap')
            normal_node.location = (-200, tex_node.location[1])
            
            # Connect texture to normal map, then to BSDF
            node_tree.links.new(tex_node.outputs['Color'], normal_node.inputs['Color'])
            node_tree.links.new(normal_node.outputs['Normal'], principled_bsdf.inputs[socket_name])
        else:
            # Direct connection for other texture types
            output_socket = 'Color' if socket_name == "Base Color" else 'Color'
            if output_socket in tex_node.outputs and socket_name in principled_bsdf.inputs:
                node_tree.links.new(tex_node.outputs[output_socket], principled_bsdf.inputs[socket_name])
    
    return new_material


@Registry.add
class TextureSetMaterialCreate(b_t.Operator):
    """Create materials from baked textures in texture set."""

    bl_idname = "pawsbkr.texture_set_material_create"
    bl_label = "Create Materials from Baked Textures"
    bl_options = {"REGISTER", "UNDO"}

    texture_set_id: b_p.StringProperty(
        name="Target texture set name", 
        default="",
        options={"HIDDEN", "SKIP_SAVE"}
    )
    
    keep_original_materials: b_p.BoolProperty(
        name="Keep Original Materials",
        description="Keep original material structure and add baked textures to it",
        default=True
    )
    
    assign_to_objects: b_p.BoolProperty(
        name="Assign to Objects",
        description="Assign the new materials to objects in the texture set",
        default=True
    )

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if not self.texture_set_id:
            raise AddonException("texture_set_id is required")

        pawsbkr = get_props(context)
        texture_set = pawsbkr.texture_sets[self.texture_set_id]
        
        if not texture_set.textures:
            self.report({"WARNING"}, "No textures found in texture set")
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Collect all baked images by texture type
        texture_images: dict[str, b_t.Image] = {}
        
        for texture_props in texture_set.textures:
            if not texture_props.is_enabled:
                continue
                
            bake_settings = get_bake_settings(context, texture_props.prop_id)
            
            # Generate expected image name (matching the baking logic)
            from .bake_common import generate_image_name_and_path
            img_name, _ = generate_image_name_and_path(
                context=context,
                settings_id=texture_props.prop_id,
                texture_set_name=texture_set.display_name,
            )
            
            # Find the image in Blender data
            image = bpy.data.images.get(img_name)
            if image:
                texture_images[bake_settings.type] = image
            else:
                self.report({"WARNING"}, f"Could not find baked image: {img_name}")
        
        if not texture_images:
            self.report({"ERROR"}, "No baked images found for texture set")
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Get all materials used by objects in the texture set
        materials_to_process: set[b_t.Material] = set()
        objects_materials: dict[str, list[b_t.Material]] = {}
        
        for mesh_props in texture_set.meshes:
            if not mesh_props.is_enabled:
                continue
                
            obj = mesh_props.get_ref()
            if not obj or obj.type != 'MESH':
                continue
                
            obj_materials = []
            for slot in obj.material_slots:
                if slot.material:
                    materials_to_process.add(slot.material)
                    obj_materials.append(slot.material)
            
            objects_materials[obj.name] = obj_materials
        
        if not materials_to_process:
            self.report({"ERROR"}, "No materials found on objects in texture set")
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Create new materials
        created_materials: dict[b_t.Material, b_t.Material] = {}
        
        for original_material in materials_to_process:
            try:
                new_material = _create_material_from_textures(
                    original_material=original_material,
                    texture_set_name=texture_set.display_name,
                    texture_images=texture_images,
                    keep_original=self.keep_original_materials
                )
                created_materials[original_material] = new_material
                self.report({"INFO"}, f"Created material: {new_material.name}")
                
            except Exception as e:
                self.report({"ERROR"}, f"Failed to create material for {original_material.name}: {str(e)}")
                continue
        
        # Assign new materials to objects if requested
        if self.assign_to_objects and created_materials:
            for obj_name, obj_materials in objects_materials.items():
                obj = bpy.data.objects.get(obj_name)
                if not obj:
                    continue
                    
                for slot_index, original_material in enumerate(obj_materials):
                    if original_material in created_materials:
                        if slot_index < len(obj.material_slots):
                            obj.material_slots[slot_index].material = created_materials[original_material]
            
            self.report({"INFO"}, f"Assigned {len(created_materials)} new materials to objects")
        
        self.report({"INFO"}, f"Successfully created {len(created_materials)} materials from baked textures")
        return {BlenderOperatorReturnType.FINISHED}

    def invoke(self, context: b_t.Context, event: b_t.Event) -> set[str]:
        """invoke() override - Show dialog for user options."""
        return context.window_manager.invoke_props_dialog(self)