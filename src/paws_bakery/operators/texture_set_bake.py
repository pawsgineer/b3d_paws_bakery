"""Bake texture set."""

from threading import Lock

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderOperatorReturnType
from ..operators.texture_set_texture_bake import TextureSetTextureBake
from ..props import TextureProps
from ..props_enums import BakeState
from ..utils import Registry, TimerManager


@Registry.add
class TextureSetBake(b_t.Operator):
    """Bake texture set."""

    bl_idname = "pawsbkr.texture_set_bake"
    bl_label = "Bake Texture Set"

    target_name: b_p.StringProperty(name="Target texture set name", default="")

    _textures: list[TextureProps] = []

    __is_running = False
    __lock = Lock()

    @classmethod
    def is_locked(cls) -> bool:
        """Returns whether the class lock is currently held."""
        return cls.__lock.locked()

    @classmethod
    def is_running(cls) -> bool:
        """Returns whether the instance of class is already active."""
        return cls.__is_running

    def _cancel(self, _context: b_t.Context) -> None:
        TimerManager.release()

        for texture in self._textures:
            texture.state = BakeState.CANCELLED.name

        self.__class__.__is_running = False  # pylint: disable=protected-access

    def _finish(self, _context: b_t.Context) -> None:
        TimerManager.release()

        self.__class__.__is_running = False  # pylint: disable=protected-access

    def modal(self, context: b_t.Context, event: b_t.Event) -> set[str]:
        """modal() override."""
        if event.type in {"ESC"}:
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        if event.type != "TIMER":
            return {BlenderOperatorReturnType.PASS_THROUGH}

        # pylint: disable-next=protected-access
        if not self.__class__.__lock.acquire(False):
            log(f"{type(self).__name__}: Skipping modal(): Already locked")
            return {BlenderOperatorReturnType.PASS_THROUGH}

        try:
            return self.__modal_lock_me(context, event)
        finally:
            self.__class__.__lock.release()  # pylint: disable=protected-access

    def __modal_lock_me(self, context: b_t.Context, _event: b_t.Event) -> set[str]:
        if (
            bpy.app.is_job_running("OBJECT_BAKE")
            or TextureSetTextureBake.is_running()
            or TextureSetTextureBake.is_locked()
        ):
            return {BlenderOperatorReturnType.PASS_THROUGH}
        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.target_name]

        texture = self._textures[0]

        if texture.state == BakeState.CANCELLED.name:
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        if texture.state == BakeState.FINISHED.name:
            self._textures.remove(texture)
            if self._textures:
                texture = self._textures[0]
            else:
                self._finish(context)
                return {BlenderOperatorReturnType.FINISHED}

        if texture.state == BakeState.QUEUED.name:
            if bpy.app.is_job_running("OBJECT_BAKE"):
                log("OBJECT_BAKE job is already running. Waiting")
            else:
                texture.state = BakeState.RUNNING.name
                # TODO: handle op return
                bpy.ops.pawsbkr.texture_set_texture_bake(
                    texture_set_name=texture_set.name,
                    texture_name=texture.name,
                )

        return {BlenderOperatorReturnType.PASS_THROUGH}

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if not self.target_name:
            raise NotImplementedError("baking without target_name not implemented")

        # TODO: Do I need a lock? Maybe execute() is thread-safe?
        # pylint: disable-next=protected-access
        if self.__class__.__is_running or not self.__class__.__lock.acquire(False):
            log(f"Cannot execute(): {self.bl_idname}. Already running")
            return {BlenderOperatorReturnType.CANCELLED}

        self.__class__.__is_running = True  # pylint: disable=protected-access
        self.__class__.__lock.release()  # pylint: disable=protected-access

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.target_name]

        if not texture_set.textures:
            self.report({"WARNING"}, "PAWSBKR: Texture set has no specified textures")
            self.__class__.__is_running = False  # pylint: disable=protected-access
            return {BlenderOperatorReturnType.CANCELLED}

        for texture in texture_set.textures:
            if not texture.is_enabled:
                continue
            texture.state = BakeState.QUEUED.name
            self._textures.append(texture)

        TimerManager.acquire()
        context.window_manager.modal_handler_add(self)

        return {BlenderOperatorReturnType.RUNNING_MODAL}

    def invoke(self, context, _event):
        """invoke() override."""
        # log(
        #     "invoke() called:",
        #     self.bl_idname,
        # )
        return self.execute(context)
