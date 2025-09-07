# Bake Settings

:::{image} ../images/ui_bake_settings.png
:align: center
:::

**Name Template**
: Template of image name.
: **Available variables**
  :::{list-table}
  :align: left

  - - **set_name**
    - Texture Set name.
  - - **size**
    - Texture Set size.
  - - **type_short**
    - Short name of type.
  - - **type_full**
    - Long name of type.
  :::

**Name Preview**
: Example of image name.

**Type**
: [](texture_types.md).

**Size**
: Texture size.

**AA**
: Antialiasing. Bake texture with incresed resolution to get smoother result.

**Samples**
: Number of samples to render. Refer to Blender docs to learn more.

**Denoise**
: Denoise the baked image. Refer to Blender docs to learn more.

**Margin**
: Extend the baked result. Refer to Blender docs to learn more.\
  [Blender Docs][bl-docs-baking-margin].

**Margin Type**
: Algorithm to extend the baked result. Refer to Blender docs to learn more.\
  [Blender Docs][bl-docs-baking-margin].

**High to Low | Selected To Active**
: Bake shading of selected objects to the active object.\
  [High to Low Baking](../source/high_to_low.md).

**Cage**
: Use cage for baking.\
  [Blender Docs][bl-docs-baking-selected].
  :::{note}
  Custom cage objects not yet implemented.
  :::

**Cage Extrusion**
: [Blender Docs][bl-docs-baking-selected].

**Ray Distance**
: [Blender Docs][bl-docs-baking-selected].

[bl-docs-baking-selected]: https://docs.blender.org/manual/en/latest/render/cycles/baking.html#selected-to-active
[bl-docs-baking-margin]: https://docs.blender.org/manual/en/latest/render/cycles/baking.html#margin
