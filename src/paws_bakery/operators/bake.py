"""Bake textures."""

from pathlib import Path
from threading import Lock

import bpy
from bpy import props as b_p
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderOperatorReturnType
from ..preferences import get_preferences
from ..props import SIMPLE_BAKE_SETTINGS_ID, BakeSettings, BakeTextureType
from ..props_enums import BakeState
from ..utils import Registry, TimerManager
from ._utils import generate_color_set, get_selected_materials
from .material_setup import MaterialNodeNames


class _BakeHelper:
    @staticmethod
    def bake(
        context: b_t.Context,
        settings: BakeSettings,
        use_clear=False,
    ) -> set[BlenderOperatorReturnType]:
        """Bake helper."""
        context.scene.render.use_lock_interface = True
        context.scene.render.engine = "CYCLES"
        context.scene.render.bake.use_pass_direct = False
        context.scene.render.bake.use_pass_indirect = False
        context.scene.render.bake.use_pass_color = True
        # TODO: parametrize use_clear?
        # context.scene.render.bake.use_clear = False

        context.scene.cycles.device = "GPU"
        context.scene.cycles.samples = settings.samples
        context.scene.cycles.use_denoising = settings.use_denoising

        return bpy.ops.object.bake(  # type: ignore[no-any-return]
            "INVOKE_DEFAULT",  # type: ignore[arg-type]
            target="IMAGE_TEXTURES",
            save_mode="INTERNAL",
            type=BakeTextureType[settings.type].cycles_type,
            width=int(settings.size) * int(settings.sampling),
            height=int(settings.size) * int(settings.sampling),
            margin=settings.margin * int(settings.sampling),
            margin_type=settings.margin_type,
            # use_split_materials=True,
            # normal_space=cfg.normal_space,
            use_selected_to_active=settings.use_selected_to_active,
            use_cage=settings.use_cage,
            cage_extrusion=settings.cage_extrusion,
            max_ray_distance=settings.max_ray_distance,
            # TODO: Reimplement using use_clear
            use_clear=use_clear,
            # TODO: implement uv_layer selection
            # uv_layer=
        )


@Registry.add
class Bake(b_t.Operator):
    """Bake map for selected objects."""

    bl_idname = "pawsbkr.bake"
    bl_label = "Bake Map"

    texture_set_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    texture_set_object_suffix: b_p.StringProperty()
    texture_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    clear_image: b_p.BoolProperty(
        default=True,
        description="Create new image instead of adding to existing",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )
    scale_image: b_p.BoolProperty(
        default=True,
        description="Scale image if AA enabled",
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    settings_id: b_p.StringProperty(
        options={"HIDDEN", "SKIP_SAVE"},  # noqa: F821
    )

    # _images: set[b_t.Image] = set()
    _image: b_t.Image = None
    _materials: dict[str, b_t.Material] = {}

    __is_running = False
    __lock = Lock()

    __og_render_use_lock_interface: bool
    __og_render_engine: str
    __og_cycles_device: str
    __og_cycles_samples: int
    __og_cycles_use_denoising: bool

    @classmethod
    def is_locked(cls) -> bool:
        """Returns whether the class lock is currently held."""
        return cls.__lock.locked()

    @classmethod
    def is_running(cls) -> bool:
        """Returns whether the instance of class is already active."""
        return cls.__is_running

    def _save_user_settings(self, context: b_t.Context) -> None:
        self.__og_render_use_lock_interface = context.scene.render.use_lock_interface
        # self.__og_render_engine = context.scene.render.engine
        self.__og_cycles_device = context.scene.cycles.device
        self.__og_cycles_samples = context.scene.cycles.samples
        self.__og_cycles_use_denoising = context.scene.cycles.use_denoising

    def _restore_user_settings(self, context: b_t.Context) -> None:
        context.scene.render.use_lock_interface = self.__og_render_use_lock_interface
        # NOTE: Setting render.engine here may lead to hardlock
        # context.scene.render.engine = self.__og_render_engine
        context.scene.cycles.device = self.__og_cycles_device
        context.scene.cycles.samples = self.__og_cycles_samples
        context.scene.cycles.use_denoising = self.__og_cycles_use_denoising

        context.window.cursor_set("DEFAULT")

    def _get_settings(self, context: b_t.Context) -> BakeSettings:
        return context.scene.pawsbkr.get_bake_settings(self.settings_id)

    def _show_image_in_editor(self, context, image):
        if context.scene.pawsbkr.utils_settings.show_image_in_editor:
            for area in context.screen.areas:
                if area.type == "IMAGE_EDITOR":
                    area.spaces.active.image = image
                    break

    def _cleanup(self) -> None:
        for mat in self._materials.values():
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)

    def _cancel(self, context: b_t.Context) -> None:
        TimerManager.release()

        if self.texture_set_id and self.texture_id:
            context.scene.pawsbkr.texture_sets[self.texture_set_id].textures[
                self.texture_id
            ].state = BakeState.CANCELLED.name

        log("PAWSBKR: Baking cancelled")

        self._restore_user_settings(context)

        self.__class__.__is_running = False  # pylint: disable=protected-access

    def _finish(self, context: b_t.Context) -> None:
        TimerManager.release()

        cfg = self._get_settings(context)

        for img in [self._image]:
            if self.scale_image and int(cfg.sampling) > 1:
                img.scale(int(cfg.size), int(cfg.size))

            img.save(quality=0)

            if context.scene.pawsbkr.utils_settings.unlink_baked_image:
                bpy.data.images.remove(img)
            else:
                self._show_image_in_editor(context, img)

        self._cleanup()

        if self.texture_set_id and self.texture_id:
            texture = context.scene.pawsbkr.texture_sets[self.texture_set_id].textures[
                self.texture_id
            ]
            texture.state = BakeState.FINISHED.name

        self._restore_user_settings(context)

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
            if bpy.app.is_job_running("OBJECT_BAKE"):
                return {BlenderOperatorReturnType.PASS_THROUGH}

            if all(img.is_dirty for img in [self._image]):
                self._finish(context)
                return {BlenderOperatorReturnType.FINISHED}

            log("Bake job not running but images appear to be unchanged")
            self.report({"ERROR"}, "Baking probably went wrong")
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        finally:
            self.__class__.__lock.release()  # pylint: disable=protected-access

    def execute(self, context: b_t.Context) -> set[str]:
        """execute() override"""
        if len(self.settings_id) < 1:
            raise ValueError("settings_id not set")

        # TODO: Do I need a lock? Maybe execute() is thread-safe?
        # pylint: disable-next=protected-access
        if self.__class__.__is_running or not self.__class__.__lock.acquire(False):
            log(f"Cannot execute(): {self.bl_idname}. Already running")
            return {BlenderOperatorReturnType.CANCELLED}

        self.__class__.__is_running = True  # pylint: disable=protected-access
        self.__class__.__lock.release()  # pylint: disable=protected-access

        if bpy.app.is_job_running("OBJECT_BAKE"):
            log("OBJECT_BAKE job is already running")
            self.report({"ERROR"}, "PAWSBKR: Baking already running")
            # TODO: wait instead of canceling?
            self.__class__.__is_running = False  # pylint: disable=protected-access
            return {BlenderOperatorReturnType.CANCELLED}

        context.window.cursor_set("WAIT")
        self._save_user_settings(context)

        cfg = self._get_settings(context)

        self._materials = get_selected_materials()

        self._cleanup()

        t_set_display_name = (
            SIMPLE_BAKE_SETTINGS_ID
            if self.texture_set_id == SIMPLE_BAKE_SETTINGS_ID
            else context.scene.pawsbkr.texture_sets[self.texture_set_id].display_name
        )
        image_name_parts = [t_set_display_name]
        if self.texture_set_object_suffix:
            image_name_parts.append(self.texture_set_object_suffix)

        image_name = cfg.get_name("_".join(image_name_parts)) + ".png"
        filepath = "/".join(
            [
                get_preferences().output_directory,
                t_set_display_name,
                image_name,
            ]
        )

        img = bpy.data.images.get(image_name)
        real_size = int(cfg.size) * int(cfg.sampling)

        if img is None and Path(bpy.path.abspath(filepath)).exists():
            img = bpy.data.images.load(filepath, check_existing=False)

        if img is None:
            # log("Creating new image")
            img = bpy.data.images.new(
                name=image_name,
                width=real_size,
                height=real_size,
                alpha=False,
                float_buffer=BakeTextureType[cfg.type].is_float,
            )
            img.filepath = filepath
        else:
            # log("Using existing image")
            if bpy.path.native_pathsep(img.filepath) != bpy.path.native_pathsep(
                filepath
            ):
                log(
                    f"Existing image with name {image_name!r} has different filepath. "
                    f"Expected: {bpy.path.native_pathsep(filepath)!r}. "
                    f"Got: {bpy.path.native_pathsep(img.filepath)!r}"
                )
                self._cancel(context)
                return {BlenderOperatorReturnType.CANCELLED}

            if self.clear_image:
                # log("Creating clear image")
                blank_img = bpy.data.images.new(
                    name=f"pawsbkr_{image_name}",
                    width=real_size,
                    height=real_size,
                    alpha=False,
                    float_buffer=BakeTextureType[cfg.type].is_float,
                )
                blank_img.filepath = filepath
                blank_img.save(quality=0)
                bpy.data.images.remove(blank_img)

                img.reload()
            elif (
                img.size[0] != real_size
                or img.size[1] != real_size
                # or img.alpha_mode is not None
                or img.is_float != BakeTextureType[cfg.type].is_float
            ):
                log(
                    f"Image with name {image_name!r} already exist but its "
                    f"parameters doesn't match: {img!r}",
                    img.size[0],
                    img.size[1],
                    img.alpha_mode,
                    img.is_float,
                )
                self._cancel(context)
                return {BlenderOperatorReturnType.CANCELLED}

        img.colorspace_settings.name = BakeTextureType[cfg.type].colorspace

        self._show_image_in_editor(context, img)

        self._image = img

        colors = generate_color_set(len(self._materials))

        for mat in self._materials.values():
            bpy.ops.pawsbkr.material_setup(target_material_name=mat.name, cleanup=True)
        for mat in self._materials.values():
            bpy.ops.pawsbkr.material_setup(
                target_material_name=mat.name,
                cleanup=False,
                target_image_name=img.name,
                mat_id_color=colors[list(self._materials.values()).index(mat)],
                texture_type=cfg.type,
                settings_id=self.settings_id,
            )

            tree = mat.node_tree
            node_name = MaterialNodeNames.BAKE_TEXTURE
            bake_texture_node = tree.nodes.get(node_name)
            # bake_texture_node.image = image
            bake_texture_node.select = True
            tree.nodes.active = bake_texture_node

        bake_result = _BakeHelper.bake(context, cfg, self.clear_image)

        if bake_result != {"RUNNING_MODAL"}:
            log("Failed to start baking:", bake_result)
            self._cancel(context)
            return {BlenderOperatorReturnType.CANCELLED}

        TimerManager.acquire()
        context.window_manager.modal_handler_add(self)

        return {BlenderOperatorReturnType.RUNNING_MODAL}
