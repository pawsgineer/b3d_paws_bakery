"""Bake texture set texture."""

import datetime
from collections import defaultdict
from threading import Lock
from typing import Sequence, cast

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderOperatorReturnType
from ..operators.bake import Bake
from ..props import MeshProps
from ..props_enums import BakeMode, BakeState
from ..utils import AddonException, Registry, TimerManager

SUFFIX_HIGH = "_high"
SUFFIX_LOW = "_low"
BAKE_COLLECTION_NAME = "pawsbakery"


@Registry.add
class TextureSetTextureBake(b_t.Operator):
    """Bake texture set texture."""

    bl_idname = "pawsbkr.texture_set_texture_bake"
    bl_label = "Bake texture set texture"

    texture_set_name: b_p.StringProperty(name="Target texture set name", default="")
    texture_name: b_p.StringProperty(name="Target texture name", default="")

    _bake_collection: b_t.Collection = None
    _meshes_active: dict[MeshProps, list[MeshProps]] = defaultdict(list[MeshProps])
    _clear_image: bool = True

    _time_start: datetime

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

    def _setup_mesh_for_baking(self, mesh: MeshProps, active: bool = False) -> None:
        mesh_ref: b_t.Object = mesh.get_ref()
        if mesh_ref is None:
            raise ValueError(f"Can not find Object with name {mesh.name!r}")

        # log("Col before:", mesh_ref.users_collection)
        if self._bake_collection not in mesh_ref.users_collection:
            self._bake_collection.objects.link(mesh_ref)
        # log("Col after:", mesh_ref.users_collection)

        mesh_ref.hide_set(False)
        mesh_ref.hide_render = False
        mesh_ref.hide_viewport = False

        viewport = cast(b_t.SpaceView3D, bpy.context.space_data)
        if not isinstance(viewport, b_t.SpaceView3D):
            raise TypeError(
                f"The context is incorrect. Expected: SpaceView3D, got {type(viewport)}"
            )
        if not mesh_ref.visible_in_viewport_get(viewport):
            mesh_ref.local_view_set(viewport, True)

        mesh_ref.select_set(True)

        if active:
            bpy.context.view_layer.objects.active = mesh_ref

        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

    def _cleanup(self) -> None:
        bake_collection = bpy.data.collections.get(BAKE_COLLECTION_NAME)
        if bake_collection is not None:
            while bake_collection.objects:
                bake_collection.objects.unlink(bake_collection.objects[0])
            bpy.data.collections.remove(bake_collection)

    def _cancel(self, context: b_t.Context) -> None:
        TimerManager.release()

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.texture_set_name]
        texture = texture_set.textures[self.texture_name]

        texture.state = BakeState.CANCELLED.name
        for active, selected in self._meshes_active.items():
            active.state = BakeState.CANCELLED.name
            for mesh in selected:
                mesh.state = BakeState.CANCELLED.name

        self._cleanup()

        self.__class__.__is_running = False  # pylint: disable=protected-access

    def _finish(self, context: b_t.Context) -> None:
        TimerManager.release()

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.texture_set_name]
        texture = texture_set.textures[self.texture_name]

        delta: datetime.timedelta = datetime.datetime.now() - self._time_start
        hours, seconds = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        texture.last_bake_time = f"{hours:02}:{minutes:02}:{seconds:02}"

        self._cleanup()

        self.__class__.__is_running = False  # pylint: disable=protected-access

    def modal(self, context: b_t.Context, event: b_t.Event) -> set[str]:
        """modal() override."""
        if event.type in {"ESC"}:
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        if event.type != "TIMER":
            return {BlenderOperatorReturnType.PASS_THROUGH}

        if not self.__class__.__lock.acquire(False):  # pylint: disable=protected-access
            log(f"{type(self).__name__}: Skipping modal(): Already locked")
            return {BlenderOperatorReturnType.PASS_THROUGH}

        try:
            return self.__modal_lock_me(context, event)
        except Exception as err:  # pylint: disable=broad-exception-caught
            log("Canceling bake. Error in __modal_lock_me():", err)
            self._cancel(context)
        finally:
            self.__class__.__lock.release()  # pylint: disable=protected-access

    def __modal_lock_me(self, context: b_t.Context, _event: b_t.Event) -> set[str]:
        if (
            bpy.app.is_job_running("OBJECT_BAKE")
            or Bake.is_running()
            or Bake.is_locked()
        ):
            # log(f"{type(self).__name__}: Skipping modal(): Bake running")
            return {BlenderOperatorReturnType.PASS_THROUGH}

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.texture_set_name]
        texture = texture_set.textures[self.texture_name]

        active, selected = list(self._meshes_active.items())[0]

        if (
            active.state != BakeState.QUEUED.name
            and texture.state == BakeState.CANCELLED.name
        ):
            log(f"Canceling: {self.bl_idname}")
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        if (
            active.state != BakeState.QUEUED.name
            and texture.state == BakeState.FINISHED.name
        ):
            for mesh in [active] + selected:
                mesh.state = BakeState.FINISHED.name

            if BakeMode[texture_set.mode] is BakeMode.SINGLE:
                self._clear_image = False
            del self._meshes_active[active]
            if self._meshes_active:
                active, selected = list(self._meshes_active.items())[0]
            else:
                self._finish(context)
                return {BlenderOperatorReturnType.FINISHED}

        if active.state == BakeState.QUEUED.name:
            if pawsbkr.utils_settings.debug_pause:
                if pawsbkr.utils_settings.debug_pause_continue:
                    pawsbkr.utils_settings.debug_pause_continue = False
                else:
                    log("debug_pause is active. skipping next bake...")
                    return {BlenderOperatorReturnType.PASS_THROUGH}

            if Bake.is_running() or bpy.app.is_job_running("OBJECT_BAKE"):
                log("OBJECT_BAKE job is already running. Waiting")
                return {BlenderOperatorReturnType.PASS_THROUGH}

            bpy.ops.object.select_all(action="DESELECT")

            # TODO: use exception on whole modal() block
            try:
                for mesh in selected:
                    # mesh.state = BakeState.RUNNING.name
                    self._setup_mesh_for_baking(mesh, False)

                self._setup_mesh_for_baking(active, True)
            except Exception as err:  # pylint: disable=broad-exception-caught
                self.report(
                    {"ERROR"},
                    f"Exception ocurred. Canceling: {self.bl_idname}. Error: {err}",
                )
                self._cancel(context)
                return {BlenderOperatorReturnType.CANCELLED}

            for mesh in [active] + selected:
                mesh.state = BakeState.RUNNING.name

            if BakeMode[texture_set.mode] is BakeMode.SINGLE:
                texture_set_object_suffix = ""
            else:
                texture_set_object_suffix = active.name

            # TODO: handle operator return
            bpy.ops.pawsbkr.bake(
                texture_set_name=texture_set.name,
                texture_set_object_suffix=texture_set_object_suffix,
                texture_name=self.texture_name,
                clear_image=self._clear_image,
                scale_image=len(self._meshes_active) < 2,
                settings_id=self.texture_name,
            )

        return {BlenderOperatorReturnType.PASS_THROUGH}

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override."""
        if not self.texture_set_name:
            raise NotImplementedError("Baking without texture_set_name not implemented")
        if not self.texture_name:
            raise NotImplementedError("Baking without texture_name not implemented")

        # TODO: Do I need a lock? Maybe execute() is thread-safe?
        # pylint: disable-next=protected-access
        if self.__class__.__is_running or not self.__class__.__lock.acquire(False):
            log(f"Cannot execute(): {self.bl_idname}. Already running")
            return {BlenderOperatorReturnType.CANCELLED}

        self.__class__.__is_running = True  # pylint: disable=protected-access
        self.__class__.__lock.release()  # pylint: disable=protected-access

        self._cleanup()

        self._bake_collection = bpy.data.collections.new(BAKE_COLLECTION_NAME)
        context.scene.collection.children.link(self._bake_collection)

        pawsbkr = context.scene.pawsbkr
        texture_set = pawsbkr.texture_sets[self.texture_set_name]
        texture = texture_set.textures[self.texture_name]
        meshes: Sequence[MeshProps] = texture_set.meshes
        bake_settings = texture.get_bake_settings()
        mode = BakeMode[texture_set.mode]

        meshes_enabled = [m for m in meshes if m.is_enabled]
        meshes_low = [m for m in meshes_enabled if SUFFIX_LOW in m.name.lower()]

        if bake_settings.match_active_by_suffix:
            for m_low in meshes_low:
                name_base = m_low.name.split(SUFFIX_LOW, 1)[0]
                high_names = [name_base, name_base + SUFFIX_HIGH]

                m_high = None
                for name in high_names:
                    m_high = meshes.get(name)
                    if m_high is not None:
                        break

                if m_high is None:
                    raise AddonException(
                        f"High poly mesh for {m_low.name!r} not found in "
                        "Texture Set mesh list"
                    )
                self._meshes_active[m_low].append(m_high)
        # TODO: implement baking of multiple objects to one object
        # else:
        #     self._meshes_active = {m: [] for m in meshes_enabled if m.is_active}

        if mode is BakeMode.SINGLE:
            if len(self._meshes_active) == 0:
                active = meshes_enabled[0]
                self._meshes_active[active] = [
                    m for m in meshes_enabled if m is not active
                ]
            elif len(self._meshes_active) == 1:
                active, selected = list(self._meshes_active.items())[0]
                if len(selected) == 0:
                    selected = [m for m in meshes_enabled if m is not active]

            for active, selected in self._meshes_active.items():
                active.state = BakeState.QUEUED.name
                for mesh in selected:
                    mesh.state = BakeState.QUEUED.name

        # elif mode is BakeMode.PER_OBJECT:
        #     # TODO: Implement PER_OBJECT bake mode
        #     if not self._meshes_active:
        #         self._meshes_active = {m: [] for m in meshes_enabled}
        #
        #     for active, selected in self._meshes_active.items():
        #         active.state = BakeState.QUEUED.name
        #         for mesh in selected:
        #             mesh.state = BakeState.QUEUED.name

        # elif mode is BakeMode.PER_MATERIAL:
        #     # TODO: Implement PER_MATERIAL bake mode
        #     raise NotImplementedError()

        else:
            raise NotImplementedError()

        self._time_start = datetime.datetime.now()

        TimerManager.acquire()
        context.window_manager.modal_handler_add(self)

        return {BlenderOperatorReturnType.RUNNING_MODAL}
