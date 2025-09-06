# High to Low Baking

## Bake Settings

```{image} ../images/ui_bake_settings.png
:align: center
```

```{list-table}
:header-rows: 1

* - Name
  - Description

* - Name Template
  - Template of image name.

* - Name Preview
  - Example render of image name.

* - Type
  - Texture [Type](#bake-types).

* - Size
  - Texture size.

* - AA
  - Antialiasing. Bake texture with incresed resolution to get smoother result.

* - Samples
  - Number of samples to render. Refer to Blender docs to learn more.

* - Denoise
  - Denoise the baked image. Refer to Blender docs to learn more.

* - Margin
  - Extend the baked result. Refer to Blender docs to learn more.

* - Margin Type
  - Algorithm to extend the baked result. Refer to Blender docs to learn more.

* - Selected To Active
  - Bake shading of selected objects to the active object.

    [High to Low Baking](#high-to-low-baking).

* - Match Active by Suffix
  - Math high and low meshes by it's suffix.

    [High to Low Baking](#high-to-low-baking).

* - Cage
  - Use cage for baking. Custom cage objects not yet implemented.

    [Blender Docs][bl-docs-baking-selected].

* - Cage Extrusion
  - [Blender Docs][bl-docs-baking-selected].

* - Ray Distance
  - [Blender Docs][bl-docs-baking-selected].
```

[bl-docs-baking-selected]: https://docs.blender.org/manual/en/latest/render/cycles/baking.html#selected-to-active
