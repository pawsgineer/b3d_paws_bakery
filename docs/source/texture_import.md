# Texture Import

The **Texture Import** helper allows you to load and assign selected images to
the material *Image Texture Nodes*.

:::{note}
[](automatic_material_creation.md) uses the same mechanism to assign baked
textures to the material, allowing customization.
:::

## Helper

You can access this helper in ***Helpers &rarr; Texture Import*** section of
the **🍰PAWSBKR** **N-Panel**

The `Batch Import Textures`/`Import Textures` buttons allow you to import images
from the file system and assign them to the selected materials.

Under the Material panel you can see the *Image Texture Nodes* that match the
[rules](preferences-texture-import) and the images assigned to them.

:::{image} ../images/ui_texture_import.png
:align: center
:::

## How it works

The add-on matches images to *Image Texture Nodes* by comparing the node name
prefix to the image name suffix, per the [rules](preferences-texture-import).

For example, a node **{sup}`(1)`** with name **{sup}`(2)`**
`texture_albedo` matches image `sf_03_01_4096_color.png` **{sup}`(3)`**
under the default rule **{sup}`(4)`**.

:::{image} ../images/ui_material_node_name.png
:align: center
:::

:::{image} ../images/ui_material_node_name_albedo_rule.png
:align: center
:::

## Customization

You can customize this process by disabling default
[rules](preferences-texture-import) and creating new ones.
