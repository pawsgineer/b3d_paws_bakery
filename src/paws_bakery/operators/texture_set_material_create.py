"""Texture Set Material Creator - DEBUG VERSION - Creates materials from baked textures."""

import bpy
from bpy import props as b_p
from bpy import types as b_t

from ..enums import BlenderOperatorReturnType
from ..props import get_bake_settings, get_props
from ..props_enums import BakeTextureType
from ..utils import AddonException, Registry


def _get_texture_type_socket_info(texture_type: str) -> dict[str, str] | None:
    """Get the appropriate material socket and output info for a texture type."""
    print(f"DEBUG: _get_texture_type_socket_info called with texture_type: '{texture_type}'")
    print(f"DEBUG: texture_type type: {type(texture_type)}")
    
    # Map texture types to BSDF socket names and texture output sockets
    socket_map = {
        BakeTextureType.DIFFUSE.name: {
            "socket": "Base Color",
            "output": "Color",
            "colorspace": "sRGB",
            "priority": 1  # Highest priority for base color
        },
        # BakeTextureType.GLOSSY.name: {
        #     "socket": "Base Color",  # Changed: Glossy should contribute to base color
        #     "output": "Color",
        #     "colorspace": "sRGB",
        #     "priority": 2,
        #     "mix_with_base": True  # Added: Should be mixed with existing base color
        # },
        BakeTextureType.NORMAL.name: {
            "socket": "Normal",
            "output": "Color",
            "colorspace": "Non-Color",
            "needs_normal_node": True,
            "priority": 2
        },
        BakeTextureType.ROUGHNESS.name: {
            "socket": "Roughness",
            "output": "Color",
            "colorspace": "Non-Color",
            "priority": 2
        },
        BakeTextureType.EMIT.name: {
            "socket": "Emission",
            "output": "Color",
            "colorspace": "sRGB",
            "priority": 2
        },
        BakeTextureType.AO.name: {
            "socket": "Base Color",  # Usually mixed with base color
            "output": "Color",
            "colorspace": "Non-Color",
            "mix_with_base": True,
            "priority": 4
        },
        # BakeTextureType.SHADOW.name: {
        #     "socket": "Base Color",
        #     "output": "Color", 
        #     "colorspace": "Non-Color",
        #     "mix_with_base": True,
        #     "priority": 5
        # },
        # BakeTextureType.COMBINED.name: {
        #     "socket": "Base Color",
        #     "output": "Color",
        #     "colorspace": "sRGB",
        #     "priority": 1
        # },
        # BakeTextureType.ENVIRONMENT.name: {
        #     "socket": "Base Color",
        #     "output": "Color",
        #     "colorspace": "sRGB",
        #     "priority": 2
        # },
        # Handle additional texture types from material_setup.py
        BakeTextureType.AORM.name: {
            "socket": "Base Color",  # AORM is a combined texture
            "output": "Color", 
            "colorspace": "Non-Color",
            "priority": 3,
            "is_packed_texture": True  # Special handling needed
        },
        BakeTextureType.EMIT_COLOR.name: {
            "socket": "Base Color",
            "output": "Color",
            "colorspace": "sRGB", 
            "priority": 1
        },
        BakeTextureType.EMIT_ROUGHNESS.name: {
            "socket": "Roughness",
            "output": "Color",
            "colorspace": "Non-Color",
            "priority": 2
        },
        BakeTextureType.EMIT_METALNESS.name: {
            "socket": "Metallic",
            "output": "Color", 
            "colorspace": "Non-Color",
            "priority": 2
        },
        BakeTextureType.EMIT_OPACITY.name: {
            "socket": "Alpha",
            "output": "Color",
            "colorspace": "Non-Color", 
            "priority": 2
        },
        BakeTextureType.MATERIAL_ID.name: {
            "socket": "Base Color",
            "output": "Color",
            "colorspace": "sRGB",
            "priority": 1
        },
        # These types typically aren't directly connected
        # BakeTextureType.POSITION.name: None,
        # BakeTextureType.UV.name: None,
        BakeTextureType.UTILS_GRID_COLOR.name: None,
        BakeTextureType.UTILS_GRID_UV.name: None,
    }
    
    print(f"DEBUG: Available socket_map keys: {list(socket_map.keys())}")
    print(f"DEBUG: BakeTextureType.DIFFUSE.name = '{BakeTextureType.DIFFUSE.name}'")
    print(f"DEBUG: BakeTextureType.ROUGHNESS.name = '{BakeTextureType.ROUGHNESS.name}'")
    
    result = socket_map.get(texture_type)
    print(f"DEBUG: socket_map.get('{texture_type}') returned: {result}")
    
    return result


def _find_principled_bsdf(material: b_t.Material) -> b_t.ShaderNodeBsdfPrincipled | None:
    """Find the Principled BSDF node in material."""
    print(f"DEBUG: _find_principled_bsdf called with material: {material.name if material else None}")
    
    if not material or not material.node_tree:
        print(f"DEBUG: Material or node_tree is None")
        return None
    
    print(f"DEBUG: Material has {len(material.node_tree.nodes)} nodes")
    for i, node in enumerate(material.node_tree.nodes):
        print(f"DEBUG: Node {i}: {node.name} (type: {node.type})")
        if node.type == "BSDF_PRINCIPLED":
            print(f"DEBUG: Found Principled BSDF node: {node.name}")
            return node
    
    print(f"DEBUG: No Principled BSDF found")
    return None


def _handle_aorm_texture(node_tree, tex_node: b_t.ShaderNodeTexImage, principled_bsdf: b_t.ShaderNodeBsdfPrincipled) -> None:
    """Handle AORM (Ambient Occlusion, Roughness, Metallic) packed texture."""
    print(f"DEBUG: _handle_aorm_texture called")
    
    # AORM textures pack data in different channels:
    # R = Ambient Occlusion
    # G = Roughness  
    # B = Metallic
    
    try:
        # Create separate RGB nodes to split channels
        separate_rgb = node_tree.nodes.new(type='ShaderNodeSeparateRGB')
        separate_rgb.location = (tex_node.location[0] + 250, tex_node.location[1])
        print(f"DEBUG: Created separate RGB node")
        
        # Connect texture to separate RGB
        node_tree.links.new(tex_node.outputs['Color'], separate_rgb.inputs['Image'])
        print(f"DEBUG: Connected texture to separate RGB")
        
        # Connect channels to appropriate BSDF inputs
        if 'Roughness' in principled_bsdf.inputs and not principled_bsdf.inputs['Roughness'].is_linked:
            node_tree.links.new(separate_rgb.outputs['G'], principled_bsdf.inputs['Roughness'])
            print(f"DEBUG: Connected G channel to Roughness")
        
        if 'Metallic' in principled_bsdf.inputs and not principled_bsdf.inputs['Metallic'].is_linked:
            node_tree.links.new(separate_rgb.outputs['B'], principled_bsdf.inputs['Metallic'])
            print(f"DEBUG: Connected B channel to Metallic")
        
        # For AO (R channel), we'll mix it with base color if not already connected
        if not principled_bsdf.inputs['Base Color'].is_linked:
            print(f"DEBUG: Creating mix node for AO")
            # Create mix node for AO
            try:
                mix_node = node_tree.nodes.new(type='ShaderNodeMixRGB')
                mix_node.blend_type = 'MULTIPLY'
                print(f"DEBUG: Created ShaderNodeMixRGB")
            except Exception as e:
                print(f"DEBUG: Failed to create ShaderNodeMixRGB, trying fallback: {e}")
                # Fallback for older Blender versions
                mix_node = node_tree.nodes.new(type='ShaderNodeMix')
                mix_node.data_type = 'RGBA'
                mix_node.blend_type = 'MULTIPLY'
                print(f"DEBUG: Created ShaderNodeMix fallback")
            
            mix_node.location = (separate_rgb.location[0] + 200, separate_rgb.location[1])
            
            # Set mix factor to 1.0 for full effect
            if 'Fac' in mix_node.inputs:
                mix_node.inputs['Fac'].default_value = 1.0
                print(f"DEBUG: Set 'Fac' to 1.0")
            elif 'Factor' in mix_node.inputs:
                mix_node.inputs['Factor'].default_value = 1.0
                print(f"DEBUG: Set 'Factor' to 1.0")
            
            # Connect AO channel to mix node
            if 'Color2' in mix_node.inputs:
                node_tree.links.new(separate_rgb.outputs['R'], mix_node.inputs['Color2'])
                print(f"DEBUG: Connected R to Color2")
            else:
                node_tree.links.new(separate_rgb.outputs['R'], mix_node.inputs[1])
                print(f"DEBUG: Connected R to input[1]")
            
            # Connect result to base color
            if 'Result' in mix_node.outputs:
                node_tree.links.new(mix_node.outputs['Result'], principled_bsdf.inputs['Base Color'])
                print(f"DEBUG: Connected Result to Base Color")
            else:
                node_tree.links.new(mix_node.outputs[0], principled_bsdf.inputs['Base Color'])
                print(f"DEBUG: Connected output[0] to Base Color")
    except Exception as e:
        print(f"DEBUG: Exception in _handle_aorm_texture: {e}")
        import traceback
        traceback.print_exc()
        raise


def _create_material_from_textures(
    original_material: b_t.Material,
    texture_set_name: str,
    texture_images: dict[str, b_t.Image],
    keep_original: bool = True
) -> b_t.Material:
    """Create a new material with baked textures connected."""
    
    print(f"DEBUG: _create_material_from_textures called")
    print(f"DEBUG: original_material: {original_material.name}")
    print(f"DEBUG: texture_set_name: {texture_set_name}")
    print(f"DEBUG: texture_images keys: {list(texture_images.keys())}")
    print(f"DEBUG: keep_original: {keep_original}")
    
    try:
        # Create new material name
        suffix = "_baked"
        new_name = f"{original_material.name}{suffix}"
        print(f"DEBUG: Initial new_name: {new_name}")
        
        # Ensure unique name
        counter = 1
        while new_name in bpy.data.materials:
            new_name = f"{original_material.name}{suffix}_{counter:03d}"
            counter += 1
            print(f"DEBUG: Trying new_name: {new_name}")
        
        print(f"DEBUG: Final new_name: {new_name}")
        
        if keep_original:
            # Copy the original material
            new_material = original_material.copy()
            new_material.name = new_name
            print(f"DEBUG: Copied original material")
        else:
            # Create a basic material
            new_material = bpy.data.materials.new(name=new_name)
            new_material.use_nodes = True
            print(f"DEBUG: Created new basic material")
            
            # Clear default nodes if creating from scratch
            new_material.node_tree.nodes.clear()
            print(f"DEBUG: Cleared default nodes")
                
            # Add basic nodes
            bsdf = new_material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
            output = new_material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
            print(f"DEBUG: Added basic BSDF and output nodes")
            
            # Position nodes
            bsdf.location = (0, 0)
            output.location = (300, 0)
            
            # Connect BSDF to output
            new_material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            print(f"DEBUG: Connected BSDF to output")
    
        # Find the Principled BSDF node
        principled_bsdf = _find_principled_bsdf(new_material)
        if not principled_bsdf:
            error_msg = f"Could not find Principled BSDF in material {new_material.name}"
            print(f"DEBUG: ERROR - {error_msg}")
            raise AddonException(error_msg)
        
        node_tree = new_material.node_tree
        print(f"DEBUG: Found principled BSDF, got node_tree")
        
        # Track nodes that mix with base color for proper positioning
        base_color_mixers = []
        texture_nodes = []
        
        # Sort textures by priority to handle base color conflicts properly
        texture_items = list(texture_images.items())
        print(f"DEBUG: texture_items before filtering: {texture_items}")
        
        # Filter out None socket_info items before sorting
        valid_items = []
        for texture_type, image in texture_items:
            print(f"DEBUG: Processing texture_type: '{texture_type}', image: {image.name}")
            socket_info = _get_texture_type_socket_info(texture_type)
            print(f"DEBUG: Got socket_info: {socket_info}")
            if socket_info:
                valid_items.append((texture_type, image, socket_info))
                print(f"DEBUG: Added to valid_items: {texture_type}")
            else:
                print(f"DEBUG: Skipped texture_type '{texture_type}' - no socket_info")
        
        print(f"DEBUG: valid_items before sorting: {[(item[0], item[2].get('priority', 999)) for item in valid_items]}")
        valid_items.sort(key=lambda x: x[2].get("priority", 999))
        print(f"DEBUG: valid_items after sorting: {[(item[0], item[2].get('priority', 999)) for item in valid_items]}")
        
        # Connect texture images to appropriate sockets
        for i, (texture_type, image, socket_info) in enumerate(valid_items):
            print(f"DEBUG: Processing texture {i+1}/{len(valid_items)}: {texture_type}")
            socket_name = socket_info["socket"]
            print(f"DEBUG: Target socket: {socket_name}")
            
            # Check if the socket exists on the Principled BSDF
            print(f"DEBUG: Available BSDF inputs: {list(principled_bsdf.inputs.keys())}")
            if socket_name not in principled_bsdf.inputs:
                warning_msg = f"Warning: Socket '{socket_name}' not found in Principled BSDF for texture type {texture_type}"
                print(f"DEBUG: {warning_msg}")
                continue
                
            # Create texture node
            print(f"DEBUG: Creating texture node for {texture_type}")
            tex_node = node_tree.nodes.new(type='ShaderNodeTexImage')
            tex_node.image = image
            tex_node.location = (-400, -len(texture_nodes) * 300)
            print(f"DEBUG: Created texture node at location {tex_node.location}")
            
            # Set appropriate colorspace
            if hasattr(tex_node.image, 'colorspace_settings'):
                tex_node.image.colorspace_settings.name = socket_info["colorspace"]
                print(f"DEBUG: Set colorspace to {socket_info['colorspace']}")
            
            texture_nodes.append(tex_node)
            
            # Special handling for AORM packed textures
            if socket_info.get("is_packed_texture", False):
                print(f"DEBUG: Handling as packed texture")
                _handle_aorm_texture(node_tree, tex_node, principled_bsdf)
                continue
            
            # Special handling for normal maps
            elif socket_info.get("needs_normal_node", False):
                print(f"DEBUG: Handling as normal map")
                # Add normal map node
                normal_node = node_tree.nodes.new(type='ShaderNodeNormalMap')
                normal_node.location = (-200, tex_node.location[1])
                print(f"DEBUG: Created normal map node")
                
                # Connect texture to normal map, then to BSDF
                node_tree.links.new(tex_node.outputs['Color'], normal_node.inputs['Color'])
                node_tree.links.new(normal_node.outputs['Normal'], principled_bsdf.inputs[socket_name])
                print(f"DEBUG: Connected normal map chain")
                
            # Special handling for textures that should mix with base color
            elif socket_info.get("mix_with_base", False):
                print(f"DEBUG: Handling as mix_with_base texture")
                # For AO, Shadow, and Glossy, we want to multiply/mix with base color
                # Use ShaderNodeMixRGB for better compatibility
                try:
                    mix_node = node_tree.nodes.new(type='ShaderNodeMixRGB')
                    # Use different blend modes for different texture types
                    if texture_type == BakeTextureType.GLOSSY.name:
                        mix_node.blend_type = 'ADD'  # Additive for glossy highlights
                        print(f"DEBUG: Created ShaderNodeMixRGB with ADD blend for glossy")
                    else:
                        mix_node.blend_type = 'MULTIPLY'  # Multiply for AO/Shadow
                        print(f"DEBUG: Created ShaderNodeMixRGB with MULTIPLY blend")
                except Exception as e:
                    print(f"DEBUG: Failed to create ShaderNodeMixRGB: {e}")
                    # Fallback for older Blender versions
                    mix_node = node_tree.nodes.new(type='ShaderNodeMix')
                    mix_node.data_type = 'RGBA'
                    if texture_type == BakeTextureType.GLOSSY.name:
                        mix_node.blend_type = 'ADD'
                        print(f"DEBUG: Created ShaderNodeMix fallback with ADD blend for glossy")
                    else:
                        mix_node.blend_type = 'MULTIPLY'
                        print(f"DEBUG: Created ShaderNodeMix fallback with MULTIPLY blend")
                
                mix_node.location = (-100, tex_node.location[1])
                
                # Set mix factor to 1.0 for full effect
                if 'Fac' in mix_node.inputs:
                    mix_node.inputs['Fac'].default_value = 1.0
                    print(f"DEBUG: Set mix 'Fac' to 1.0")
                elif 'Factor' in mix_node.inputs:
                    mix_node.inputs['Factor'].default_value = 1.0
                    print(f"DEBUG: Set mix 'Factor' to 1.0")
                
                # Connect texture to mix node
                print(f"DEBUG: Mix node inputs: {list(mix_node.inputs.keys())}")
                if 'Color2' in mix_node.inputs:
                    node_tree.links.new(tex_node.outputs['Color'], mix_node.inputs['Color2'])
                    print(f"DEBUG: Connected texture to Color2")
                else:
                    # Try alternative input names
                    node_tree.links.new(tex_node.outputs['Color'], mix_node.inputs[1])
                    print(f"DEBUG: Connected texture to input[1]")
                
                base_color_mixers.append((mix_node, tex_node))
                print(f"DEBUG: Added to base_color_mixers")
                
            else:
                print(f"DEBUG: Handling as direct connection")
                # Direct connection for other texture types
                output_socket = socket_info["output"]
                print(f"DEBUG: output_socket: {output_socket}")
                print(f"DEBUG: tex_node.outputs keys: {list(tex_node.outputs.keys())}")
                print(f"DEBUG: principled_bsdf.inputs keys: {list(principled_bsdf.inputs.keys())}")
                
                if (output_socket in tex_node.outputs and 
                    socket_name in principled_bsdf.inputs):
                    
                    # Check if socket is already connected (avoid conflicts)
                    if not principled_bsdf.inputs[socket_name].is_linked:
                        node_tree.links.new(tex_node.outputs[output_socket], principled_bsdf.inputs[socket_name])
                        print(f"DEBUG: Connected {output_socket} to {socket_name}")
                    else:
                        warning_msg = f"Warning: Socket '{socket_name}' already connected, skipping {texture_type}"
                        print(f"DEBUG: {warning_msg}")
                else:
                    error_msg = f"DEBUG: Could not connect - missing socket. output_socket in outputs: {output_socket in tex_node.outputs}, socket_name in inputs: {socket_name in principled_bsdf.inputs}"
                    print(error_msg)
        
        # Handle base color mixing for AO/Shadow/Glossy textures
        print(f"DEBUG: Processing base_color_mixers, count: {len(base_color_mixers)}")
        if base_color_mixers:
            # Find if we have a direct diffuse texture
            diffuse_connected = False
            diffuse_output = None
            
            for texture_type, image, socket_info in valid_items:
                print(f"DEBUG: Checking for diffuse texture: {texture_type}, socket: {socket_info['socket']}, mix_with_base: {socket_info.get('mix_with_base', False)}")
                if (socket_info["socket"] == "Base Color" and 
                    not socket_info.get("mix_with_base", False) and
                    not socket_info.get("is_packed_texture", False)):
                    diffuse_connected = True
                    print(f"DEBUG: Found direct diffuse texture: {texture_type}")
                    # Find the corresponding texture node
                    for tex_node in texture_nodes:
                        if tex_node.image == image:
                            diffuse_output = tex_node.outputs['Color']
                            print(f"DEBUG: Found diffuse texture node output")
                            break
                    break
            
            print(f"DEBUG: diffuse_connected: {diffuse_connected}")
            
            # Chain the mix nodes
            current_input = diffuse_output if diffuse_connected else None
            print(f"DEBUG: Starting with current_input: {current_input}")
            
            for j, (mix_node, tex_node) in enumerate(base_color_mixers):
                print(f"DEBUG: Processing base color mixer {j+1}/{len(base_color_mixers)}")
                if current_input:
                    print(f"DEBUG: Mix node inputs: {list(mix_node.inputs.keys())}")
                    if 'Color1' in mix_node.inputs:
                        node_tree.links.new(current_input, mix_node.inputs['Color1'])
                        print(f"DEBUG: Connected current_input to Color1")
                    else:
                        node_tree.links.new(current_input, mix_node.inputs[0])
                        print(f"DEBUG: Connected current_input to input[0]")
                else:
                    print(f"DEBUG: No current_input to connect")
                
                print(f"DEBUG: Mix node outputs: {list(mix_node.outputs.keys())}")
                if 'Result' in mix_node.outputs:
                    current_input = mix_node.outputs['Result']
                    print(f"DEBUG: Updated current_input to Result output")
                else:
                    current_input = mix_node.outputs[0]
                    print(f"DEBUG: Updated current_input to output[0]")
            
            # Connect final result to Base Color if no direct diffuse is connected
            if current_input and not principled_bsdf.inputs['Base Color'].is_linked:
                node_tree.links.new(current_input, principled_bsdf.inputs['Base Color'])
                print(f"DEBUG: Connected final mixer result to Base Color")
            else:
                print(f"DEBUG: Not connecting final result - current_input: {current_input}, Base Color linked: {principled_bsdf.inputs['Base Color'].is_linked}")
        
        print(f"DEBUG: Material creation completed successfully")
        return new_material
        
    except Exception as e:
        print(f"DEBUG: Exception in _create_material_from_textures: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up any partially created material
        if 'new_material' in locals() and new_material:
            try:
                bpy.data.materials.remove(new_material)
                print(f"DEBUG: Cleaned up partially created material")
            except Exception as cleanup_e:
                print(f"DEBUG: Failed to cleanup material: {cleanup_e}")
                pass
        raise AddonException(f"Failed to create material from textures: {str(e)}")


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
        print(f"DEBUG: TextureSetMaterialCreate.execute() called")
        print(f"DEBUG: texture_set_id: '{self.texture_set_id}'")
        
        if not self.texture_set_id:
            error_msg = "texture_set_id is required"
            print(f"DEBUG: ERROR - {error_msg}")
            raise AddonException(error_msg)

        pawsbkr = get_props(context)
        print(f"DEBUG: Got pawsbkr props")
        
        texture_set = pawsbkr.texture_sets[self.texture_set_id]
        print(f"DEBUG: Got texture_set: {texture_set.display_name}")
        print(f"DEBUG: texture_set.textures count: {len(texture_set.textures)}")
        
        if not texture_set.textures:
            warning_msg = "No textures found in texture set"
            print(f"DEBUG: WARNING - {warning_msg}")
            self.report({"WARNING"}, warning_msg)
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Collect all baked images by texture type
        texture_images: dict[str, b_t.Image] = {}
        images_found = []
        images_missing = []
        
        for i, texture_props in enumerate(texture_set.textures):
            print(f"DEBUG: Processing texture {i+1}/{len(texture_set.textures)}: enabled={texture_props.is_enabled}, prop_id={texture_props.prop_id}")
            
            if not texture_props.is_enabled:
                print(f"DEBUG: Skipping disabled texture")
                continue
                
            bake_settings = get_bake_settings(context, texture_props.prop_id)
            print(f"DEBUG: Got bake_settings: type={bake_settings.type}")
            
            # Generate expected image name (matching the baking logic)
            from .bake_common import generate_image_name_and_path
            img_name, _ = generate_image_name_and_path(
                context=context,
                settings_id=texture_props.prop_id,
                texture_set_name=texture_set.display_name,
            )
            print(f"DEBUG: Expected image name: {img_name}")
            
            # Find the image in Blender data
            print(f"DEBUG: Available images in bpy.data.images: {[img.name for img in bpy.data.images]}")
            image = bpy.data.images.get(img_name)
            if image:
                texture_images[bake_settings.type] = image
                images_found.append(f"{bake_settings.type}: {img_name}")
                print(f"DEBUG: Found image for type {bake_settings.type}")
            else:
                images_missing.append(f"{bake_settings.type}: {img_name}")
                print(f"DEBUG: Missing image for type {bake_settings.type}")
        
        print(f"DEBUG: Final texture_images mapping: {[(k, v.name) for k, v in texture_images.items()]}")
        
        # Report what we found
        if images_found:
            info_msg = f"Found {len(images_found)} baked images: {', '.join(images_found)}"
            print(f"DEBUG: {info_msg}")
            self.report({"INFO"}, info_msg)
        
        if images_missing:
            warning_msg = f"Missing {len(images_missing)} baked images: {', '.join(images_missing)}"
            print(f"DEBUG: {warning_msg}")
            self.report({"WARNING"}, warning_msg)
        
        if not texture_images:
            error_msg = "No baked images found for texture set. Make sure to bake textures first."
            print(f"DEBUG: ERROR - {error_msg}")
            self.report({"ERROR"}, error_msg)
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Get all materials used by objects in the texture set
        materials_to_process: set[b_t.Material] = set()
        objects_materials: dict[str, list[b_t.Material]] = {}
        
        print(f"DEBUG: Processing meshes in texture set, count: {len(texture_set.meshes)}")
        for i, mesh_props in enumerate(texture_set.meshes):
            print(f"DEBUG: Processing mesh {i+1}/{len(texture_set.meshes)}: {mesh_props.name}, enabled={mesh_props.is_enabled}")
            
            if not mesh_props.is_enabled:
                print(f"DEBUG: Skipping disabled mesh")
                continue
                
            obj = mesh_props.get_ref()
            print(f"DEBUG: Got object reference: {obj.name if obj else None}, type: {obj.type if obj else None}")
            
            if not obj or obj.type != 'MESH':
                warning_msg = f"Object {mesh_props.name} not found or not a mesh"
                print(f"DEBUG: WARNING - {warning_msg}")
                self.report({"WARNING"}, warning_msg)
                continue
                
            obj_materials = []
            print(f"DEBUG: Object has {len(obj.material_slots)} material slots")
            for j, slot in enumerate(obj.material_slots):
                print(f"DEBUG: Material slot {j}: {slot.material.name if slot.material else 'None'}")
                if slot.material:
                    materials_to_process.add(slot.material)
                    obj_materials.append(slot.material)
            
            if obj_materials:
                objects_materials[obj.name] = obj_materials
                print(f"DEBUG: Added {len(obj_materials)} materials for object {obj.name}")
            else:
                warning_msg = f"Object {obj.name} has no materials"
                print(f"DEBUG: WARNING - {warning_msg}")
                self.report({"WARNING"}, warning_msg)
        
        print(f"DEBUG: Total materials to process: {len(materials_to_process)}")
        print(f"DEBUG: Materials: {[mat.name for mat in materials_to_process]}")
        
        if not materials_to_process:
            error_msg = "No materials found on objects in texture set"
            print(f"DEBUG: ERROR - {error_msg}")
            self.report({"ERROR"}, error_msg)
            return {BlenderOperatorReturnType.CANCELLED}
        
        # Create new materials
        created_materials: dict[b_t.Material, b_t.Material] = {}
        
        for i, original_material in enumerate(materials_to_process):
            print(f"DEBUG: Creating material {i+1}/{len(materials_to_process)}: {original_material.name}")
            try:
                new_material = _create_material_from_textures(
                    original_material=original_material,
                    texture_set_name=texture_set.display_name,
                    texture_images=texture_images,
                    keep_original=self.keep_original_materials
                )
                created_materials[original_material] = new_material
                success_msg = f"Created material: {new_material.name}"
                print(f"DEBUG: SUCCESS - {success_msg}")
                self.report({"INFO"}, success_msg)
                
            except Exception as e:
                error_msg = f"Failed to create material for {original_material.name}: {str(e)}"
                print(f"DEBUG: ERROR - {error_msg}")
                print(f"DEBUG: Detailed error for {original_material.name}: {str(e)}")
                import traceback
                traceback.print_exc()
                self.report({"ERROR"}, error_msg)
                continue
        
        print(f"DEBUG: Successfully created {len(created_materials)} materials")
        
        # Assign new materials to objects if requested
        if self.assign_to_objects and created_materials:
            print(f"DEBUG: Assigning materials to objects")
            assigned_count = 0
            for obj_name, obj_materials in objects_materials.items():
                obj = bpy.data.objects.get(obj_name)
                print(f"DEBUG: Processing object {obj_name}, found: {obj is not None}")
                if not obj:
                    continue
                    
                for slot_index, original_material in enumerate(obj_materials):
                    print(f"DEBUG: Slot {slot_index}, original material: {original_material.name}")
                    if original_material in created_materials:
                        if slot_index < len(obj.material_slots):
                            old_name = obj.material_slots[slot_index].material.name if obj.material_slots[slot_index].material else "None"
                            obj.material_slots[slot_index].material = created_materials[original_material]
                            new_name = created_materials[original_material].name
                            print(f"DEBUG: Assigned slot {slot_index}: {old_name} -> {new_name}")
                            assigned_count += 1
                        else:
                            print(f"DEBUG: Slot {slot_index} out of range for object {obj_name}")
                    else:
                        print(f"DEBUG: No created material found for {original_material.name}")
            
            info_msg = f"Assigned {assigned_count} material slots to {len(objects_materials)} objects"
            print(f"DEBUG: {info_msg}")
            self.report({"INFO"}, info_msg)
        else:
            print(f"DEBUG: Skipping material assignment - assign_to_objects: {self.assign_to_objects}, created_materials count: {len(created_materials)}")
        
        final_msg = f"Successfully created {len(created_materials)} materials from {len(texture_images)} texture types"
        print(f"DEBUG: FINAL SUCCESS - {final_msg}")
        self.report({"INFO"}, final_msg)
        return {BlenderOperatorReturnType.FINISHED}

    def invoke(self, context: b_t.Context, event: b_t.Event) -> set[str]:
        """invoke() override - Show dialog for user options."""
        print(f"DEBUG: TextureSetMaterialCreate.invoke() called")
        return context.window_manager.invoke_props_dialog(self)