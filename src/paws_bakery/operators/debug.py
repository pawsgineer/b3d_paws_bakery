"""Init material utils."""

from bpy import types as b_t

from ..enums import BlenderOperatorReturnType
from ..utils import Registry, TimerManager
from .bake import Bake
from .texture_set_bake import TextureSetBake
from .texture_set_texture_bake import TextureSetTextureBake


@Registry.add
class DebugResetState(b_t.Operator):
    r"""Tries to reset addon state. Expect the unexpected ¯\_(ツ)_/¯"""

    bl_idname = "pawsbkr.debug_reset_state"
    bl_label = "Reset Addon State"
    bl_options = {"REGISTER"}

    def execute(self, _context: b_t.Context) -> set[str]:
        """execute() override."""
        # pylint: disable=protected-access
        TimerManager._TimerManager__ref_count = 0
        TimerManager._TimerManager__remove_timer()
        Bake._Bake__is_running = False
        TextureSetTextureBake._TextureSetTextureBake__is_running = False
        TextureSetBake._TextureSetBake__is_running = False
        # pylint: enable=protected-access

        return {BlenderOperatorReturnType.FINISHED}
