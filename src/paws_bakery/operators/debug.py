"""Init material utils."""

from bpy import types as blt

from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderOperatorType as BOT
from ..utils import Registry, TimerManager


@Registry.add
class DebugResetState(blt.Operator):
    r"""Tries to reset addon state. Expect the unexpected ¯\_(ツ)_/¯."""

    bl_idname = "pawsbkr.debug_reset_state"
    bl_label = "Reset Addon State"
    bl_options = {BOT.REGISTER}

    def execute(self, _context: blt.Context) -> set[str]:  # noqa: D102
        # pylint: disable=protected-access
        TimerManager._TimerManager__ref_count = 0  # type: ignore[attr-defined]
        TimerManager._TimerManager__remove_timer()  # type: ignore[attr-defined]
        # BakeSelected._Bake__is_running = False
        # TextureSetBake._TextureSetTextureBake__is_running = False
        # pylint: enable=protected-access

        return {BORT.FINISHED}
