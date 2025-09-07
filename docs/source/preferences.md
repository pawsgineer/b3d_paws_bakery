# Preferences

## Scene

All settings available in the **🍰PAWSBKR** **N-Panel**, including defined
**Texture Sets**, are applied and stored in the Scene properties.

:::{warning}
This means that if you delete a Scene that has Texture Sets and other settings
added to it, you will loose all those settings.
:::

:::{image} ../images/ui_settings_scene.png
:align: center
:::

**Unlink Baked Image**
: Unlinks image from current **.blend** file after bake.

**Show Baked Image In Editor**
: Display the baked image in the **Image Editor** area, if available.\
  Disabling this may help avoid some crashes, especially in earlier versions of Blender.

**Material Creation**
: See [](automatic_material_creation.md)

## Add-on preferences

This settings located in
***Edit &rarr; Preferences &rarr; Add-ons &rarr; PAWS: Bakery***.

### General

:::{image} ../images/ui_preferences_general.png
:align: center
:::

**Output Directory**
: Path to directory where to save baked textures

**Enable Debug Tools**
: Used for development. You don't want to touch that.

(preferences-texture-import)=
### Texture Import Rules

This section allows you to disable built-in [](texture_import.md) rules or
create your own.

:::{image} ../images/ui_preferences_texture_import.png
:align: center
:::

**Node Name Prefix**
: Prefix of **Shader Node** names to look for.

**Aliases**
: List of suffixes to look for in image names to match it with a **Shader Node**.

**Non-Color**
: Either imported image should have **Colorspace** value set to `Non-Color` or `Default`.
