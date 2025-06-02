"""Workaround for Blender icons versioning."""

import bpy

STRIP_COLOR_01 = "SEQUENCE_COLOR_01" if bpy.app.version < (4, 4) else "STRIP_COLOR_01"
STRIP_COLOR_02 = "SEQUENCE_COLOR_02" if bpy.app.version < (4, 4) else "STRIP_COLOR_02"
STRIP_COLOR_03 = "SEQUENCE_COLOR_03" if bpy.app.version < (4, 4) else "STRIP_COLOR_03"
STRIP_COLOR_04 = "SEQUENCE_COLOR_04" if bpy.app.version < (4, 4) else "STRIP_COLOR_04"
