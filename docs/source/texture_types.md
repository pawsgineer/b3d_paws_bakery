# Texture Types

:::{image} ../images/ui_texture_types.png
:align: center
:::

A popular approach to baking *Color*, *Metalness* and *Roughness* in Blender involves
using float value as input to the *Emit* shader and the Blender *Emit* bake type.\
In most cases, you'll likely want to use this approach instead of the native *Diffuse*
and *Roughness*.

:::{seealso}
[Blender Bake Types][bl-docs-baking-settings].
:::

[bl-docs-baking-settings]: https://docs.blender.org/manual/en/latest/render/cycles/baking.html#settings

:::{list-table}
:align: left

- - Emit
  - Bake material output in Emit mode

- - Color(Emit)
  - Bake color value as Emit output

- - Roughness(Emit)
  - Bake roughness value as Emit output

- - Metalness(Emit)
  - Bake metalness value as Emit output

- - Opacity(Emit)
  - Bake opacity value as Emit output

- - Diffuse
  - Bake material output in Diffuse mode

- - Roughness
  - Bake material output in Roughness mode

- - Normal
  - Bake material output in Normal mode

- - Material ID
  - Bake Material ID map

- - AO
  - Bake Ambient Oclussion map

- - AORM
  - Bake packed Ambient Oclussion, Roughness, Metalness map

- - Utils: Grid Color
  - Bake color grid map

- - Utils: Grid UV
  - Bake UV grid map

- - Combined
  - Bake material output in Combined mode

- - Shadow
  - Bake material output in Shadow mode

- - Position
  - Bake material output in Position mode

- - UV
  - Bake material output in UV mode

- - Environment
  - Bake material output in Environment mode

- - Glossy
  - Bake material output in Glossy mode

- - Transmission
  - Bake material output Transmission mode
:::
