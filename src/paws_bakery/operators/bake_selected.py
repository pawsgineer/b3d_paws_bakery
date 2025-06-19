"""Bake textures."""

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderEventType, BlenderJobType, BlenderOperatorReturnType
from ..props import SIMPLE_BAKE_SETTINGS_ID, get_bake_settings
from ..utils import Registry, TimerManager
from .bake_common import BakeObjects, generate_image_name_and_path
from .bake_job import BakeJob, BakeJobState
from .bake_manager import BakeManager


@Registry.add
class BakeSelected(b_t.Operator):
    """Bake texture map for selected objects."""

    bl_idname = "pawsbkr.bake"
    bl_label = "Bake Map"

    clear_image: b_p.BoolProperty(  # type: ignore[valid-type]
        default=True,
        description="Create new image instead of adding to existing",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    scale_image: b_p.BoolProperty(  # type: ignore[valid-type]
        default=True,
        description="Scale image if AA enabled",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    settings_id = SIMPLE_BAKE_SETTINGS_ID

    __bake_job: BakeJob

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if BakeManager.is_running():
            log(f"{self.bl_idname}: execute() failed: Already running")
            return {BlenderOperatorReturnType.CANCELLED}

        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            log("`OBJECT_BAKE` job is already running")
            self.report({"ERROR"}, "PAWSBKR: Baking already running")
            return {BlenderOperatorReturnType.CANCELLED}

        img_name, img_path = generate_image_name_and_path(
            context=context,
            settings_id=self.settings_id,
            texture_set_name=SIMPLE_BAKE_SETTINGS_ID,
        )

        if context.active_object is None:
            self.report({"ERROR"}, "PAWSBKR: No active Object")
            return {BlenderOperatorReturnType.CANCELLED}

        objects = BakeObjects(
            active=context.active_object, selected=context.selected_objects
        )

        self.__bake_job = BakeJob(
            context=context,
            objects=objects,
            settings=get_bake_settings(context, self.settings_id),
            clear_image=self.clear_image,
            scale_image=self.scale_image,
            image_name=img_name,
            image_path=img_path,
        )
        self.__bake_job.on_execute()

        TimerManager.acquire()
        context.window_manager.modal_handler_add(self)

        return {BlenderOperatorReturnType.RUNNING_MODAL}

    def modal(self, context: b_t.Context, event: b_t.Event) -> set[str]:
        """modal() override."""
        if event.type in {BlenderEventType.ESC}:
            self.__cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        if event.type != BlenderEventType.TIMER:
            return {BlenderOperatorReturnType.PASS_THROUGH}

        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            return {BlenderOperatorReturnType.PASS_THROUGH}

        result = self.__bake_job.on_modal()

        if result is BakeJobState.RUNNING:
            return {BlenderOperatorReturnType.PASS_THROUGH}
        if result is BakeJobState.FINISHED:
            self.__finish(context)
            return {BlenderOperatorReturnType.FINISHED}

        self.report({"ERROR"}, "Baking went wrong")
        self.__cancel(context)
        return {BlenderOperatorReturnType.CANCELLED}

    def __cancel(self, _context: b_t.Context) -> None:
        TimerManager.release()
        self.__bake_job.cancel()

    # pylint: disable-next=no-self-use
    def __finish(self, _context: b_t.Context) -> None:
        TimerManager.release()
