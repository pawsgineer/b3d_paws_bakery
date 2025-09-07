# High to Low Baking

## Simple Mode

In **Simple Mode** high-to-low poly baking works the same as vanila Blender.

1. Set the desired texture [](./bake_settings.md).
2. Toggle on the `Selected to Active` checkbox in the
   [Simple Mode](quick-start-simple-mode) Panel.
3. Select the objects in 3D Viewport. *low* object must be active (selected last).
4. Click the `BAKE SELECTED` button.

:::{seealso}
[Blender Bake Selected to Active][bl-docs-baking-selected].
:::

[bl-docs-baking-selected]: <https://docs.blender.org/manual/en/latest/render/cycles/baking.html#selected-to-active>

## Texture Set Mode

In **Texture Set Mode**, objects are matched using `_high`/`_low` name suffixes.

When matching, everything after the `_high` suffix in the name is omitted,
allowing baking many *high* objects into one *low*.

For example, objects set up as shown in the image below would result in 3 *low* objects.

:::{image} ../images/ui_texture_set_objects.png
:align: center
:::
