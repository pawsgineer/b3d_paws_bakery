# flake8: noqa: F821
"""Bake texture set."""

import datetime
from itertools import chain

import bpy
from bpy import props as blp
from bpy import types as blt

from .._helpers import log, log_err
from ..common import match_low_to_high
from ..enums import BlenderEventType, BlenderJobType
from ..enums import BlenderOperatorReturnType as BORT
from ..enums import BlenderWMReportType as BWMRT
from ..props import (
    TextureProps,
    TextureSetProps,
    get_bake_settings,
    get_props,
)
from ..props_enums import BakeMode, BakeState
from ..utils import Registry, TimerManager
from .bake_common import (
    BakeObjects,
    generate_image_name_and_path,
)
from .bake_job import BakeJob, BakeJobState
from .bake_manager import BakeManager
from .texture_set_material_create import create_materials


@Registry.add
class TextureSetBake(blt.Operator):
    """Bake texture set textures."""

    bl_idname = "pawsbkr.texture_set_bake"
    bl_label = "Bake Texture Set Textures"

    texture_set_id: blp.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},
    )
    texture_id: blp.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN", "SKIP_SAVE"},
    )

    _clear_image: bool = True

    _time_start: datetime.datetime

    _texture_set: TextureSetProps
    _bake_textures: list[TextureProps]
    _bake_objects_list: list[BakeObjects]

    __bake_job: BakeJob | None = None

    def execute(  # noqa: D102
        self, context: blt.Context
    ) -> set[BORT]:
        can_run, msg = self.__can_run()
        if not can_run:
            log(msg)
            return {BORT.CANCELLED}

        self._texture_set = get_props(context).texture_sets[self.texture_set_id]

        self._bake_textures = []
        if self.texture_id:
            texture = self._texture_set.textures[self.texture_id]
            self._bake_textures.append(texture)
        else:
            for texture in self._texture_set.get_enabled_textures():
                self._bake_textures.append(texture)

        for texture in self._bake_textures:
            texture.state = BakeState.QUEUED.name

        self.__prepare_bake_objects(context, self._bake_textures[0])

        self._time_start = datetime.datetime.now()

        TimerManager.acquire()
        context.window_manager.modal_handler_add(self)

        return {BORT.RUNNING_MODAL}

    def modal(  # noqa: D102
        self, context: blt.Context, event: blt.Event
    ) -> set[BORT]:
        if event.type in {BlenderEventType.ESC}:
            self._cancel(context)
            return {BORT.CANCELLED}

        if event.type != BlenderEventType.TIMER or bpy.app.is_job_running(
            BlenderJobType.OBJECT_BAKE
        ):
            return {BORT.PASS_THROUGH}

        bake_job = self.__ensure_bake_job(context)
        job_state = bake_job.on_modal()

        return self.__handle_job_state(context, job_state)

    def __can_run(self) -> tuple[bool, str]:
        msg: str = ""
        if not self.texture_set_id:
            raise NotImplementedError("Baking without texture_set_id not implemented")
        if not self.texture_id:
            log("texture_id not set. Baking all Textures in Texture Set")
            # raise NotImplementedError("Baking without texture_id not implemented")

        if BakeManager.is_running():
            msg = f"{self.bl_idname}: execute() failed: Already running"
        elif bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            msg = "OBJECT_BAKE job is already running"
            self.report({BWMRT.ERROR}, "PAWSBKR: Baking already running")
            # TODO: wait instead of canceling?
        else:
            return True, msg

        return False, msg

    def __prepare_bake_objects(
        self, context: blt.Context, texture: TextureProps
    ) -> None:
        bake_settings = get_bake_settings(context, texture.prop_id)

        meshes_enabled = self._texture_set.get_enabled_meshes()

        self._bake_objects_list = []

        if (
            bake_settings.use_selected_to_active
            and bake_settings.match_active_by_suffix
        ):
            matching_names = match_low_to_high([m.name for m in meshes_enabled])
            for low_high_map in matching_names:
                active = self._texture_set.meshes[low_high_map.low].ensure_mesh_ref()
                self._bake_objects_list.append(
                    BakeObjects(
                        active=active,
                        selected=[
                            active,
                            *(
                                self._texture_set.meshes[name].ensure_mesh_ref()
                                for name in low_high_map.high
                            ),
                        ],
                    )
                )
        else:
            for mesh in meshes_enabled:
                mesh_ref = mesh.ensure_mesh_ref()
                self._bake_objects_list.append(
                    BakeObjects(active=mesh_ref, selected=[mesh_ref])
                )

        for mesh in meshes_enabled:
            mesh.state = BakeState.QUEUED.name

    def __ensure_bake_job(self, context: blt.Context) -> BakeJob:
        return self.__bake_job or self.__bake_next(context)

    def __handle_job_state(
        self, context: blt.Context, state: BakeJobState
    ) -> set[BORT]:
        if state is BakeJobState.RUNNING:
            return {BORT.PASS_THROUGH}

        if state is BakeJobState.CANCELED:
            log("Canceling: reason BakeJobState.CANCELED")
            self._cancel(context)
            return {BORT.CANCELLED}

        if state is BakeJobState.FINISHED:
            return self.__handle_job_state_finished(context)

        self.report({BWMRT.ERROR}, "Baking went wrong")
        self._cancel(context)
        return {BORT.CANCELLED}

    def __handle_job_state_finished(self, context: blt.Context) -> set[BORT]:
        pawsbkr = get_props(context)

        bake_objects = self._bake_objects_list[0]
        for mesh in chain([bake_objects.active], bake_objects.selected):
            self._texture_set.meshes[mesh.name].state = BakeState.FINISHED.name

        if pawsbkr.utils_settings.debug_pause:
            if pawsbkr.utils_settings.debug_pause_continue:
                pawsbkr.utils_settings.debug_pause_continue = False
            else:
                log("debug_pause is active. skipping next bake...")
                return {BORT.PASS_THROUGH}

        if BakeMode[self._texture_set.mode] is BakeMode.SINGLE:
            self._clear_image = False

        del self._bake_objects_list[0]
        if not self._bake_objects_list:
            self._finish_texture(context)
            if not self._bake_textures:
                self._finish(context)
                return {BORT.FINISHED}

            self.__prepare_bake_objects(context, self._bake_textures[0])

        self.__bake_next(context)

        return {BORT.PASS_THROUGH}

    def __bake_next(self, context: blt.Context) -> BakeJob:
        self._bake_textures[0].state = BakeState.RUNNING.name

        bake_objects = self._bake_objects_list[0]
        for mesh in chain([bake_objects.active], bake_objects.selected):
            self._texture_set.meshes[mesh.name].state = BakeState.RUNNING.name

        if BakeMode[self._texture_set.mode] is BakeMode.PER_OBJECT:
            object_prefix = bake_objects.active.name
        else:
            object_prefix = ""
        img_name, img_path = generate_image_name_and_path(
            context=context,
            settings_id=self._bake_textures[0].prop_id,
            texture_set_name=self._texture_set.display_name,
            object_prefix=object_prefix,
        )

        self.__bake_job = BakeJob(
            context=context,
            objects=bake_objects,
            settings=get_bake_settings(context, self._bake_textures[0].prop_id),
            clear_image=self._clear_image,
            scale_image=len(self._bake_objects_list) < 2,
            image_name=img_name,
            image_path=img_path,
        )
        self.__bake_job.on_execute()
        return self.__bake_job

    def _cancel(self, _context: blt.Context) -> None:
        TimerManager.release()

        if self.__bake_job is not None:
            self.__bake_job.cancel()

        for texture in self._bake_textures:
            texture.state = BakeState.CANCELLED.name

        for bake_objects in self._bake_objects_list:
            for mesh in chain([bake_objects.active], bake_objects.selected):
                self._texture_set.meshes[mesh.name].state = BakeState.CANCELLED.name

    def _finish_texture(self, _context: blt.Context) -> None:
        delta: datetime.timedelta = datetime.datetime.now() - self._time_start
        minutes, seconds = divmod(delta.seconds, 60)

        self._bake_textures[0].last_bake_time = f"{minutes:02}:{seconds:02}"
        self._bake_textures[0].state = BakeState.FINISHED.name
        del self._bake_textures[0]

        self._clear_image = True
        self._time_start = datetime.datetime.now()

    def _finish(self, context: blt.Context) -> None:
        TimerManager.release()

        if self._texture_set.create_materials:
            try:
                create_materials(context=context, texture_set=self._texture_set)
            # pylint: disable-next=broad-exception-caught
            except Exception as ex:
                msg = f"Failed to create materials: {ex}"
                log_err(msg, with_tb=True)
                self.report({BWMRT.ERROR}, msg)
