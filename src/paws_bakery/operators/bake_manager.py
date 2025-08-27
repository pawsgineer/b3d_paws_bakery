"""Manages scene, materials setup and Blender's bake operator."""

from collections.abc import Sequence
from dataclasses import dataclass, field

import bpy
from bpy import types as b_t

from .._helpers import log, log_err
from ..enums import BlenderJobType, BlenderOperatorReturnType
from ..props import BakeSettings, BakeTextureType, get_props_wm
from ..utils import AddonException
from ._utils import generate_color_set, get_objects_materials
from .bake_common import BakeObjects
from .material_setup import (
    BakeMaterialManager,
    MaterialNodeNames,
    material_cleanup,
)

TMP_SCENE_NAME = "pawsbkr_tmp"
BAKE_COLLECTION_NAME = TMP_SCENE_NAME

_EDITOR_MODE = "OBJECT"
_RENDER_ENGINE = "CYCLES"


def call_bake_op(
    settings: BakeSettings, *, use_clear: bool = False, uv_layer: str = ""
) -> set[BlenderOperatorReturnType]:
    """Call bpy.ops.object.bake using provided BakeSettings."""
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
        use_clear=use_clear,
        uv_layer=uv_layer,
    )


def _materials_cleanup(materials: Sequence[b_t.Material]) -> None:
    for mat in materials:
        material_cleanup(mat)


def _materials_setup(
    materials: Sequence[b_t.Material],
    settings: BakeSettings,
    image: b_t.Image,
) -> None:
    for mat in materials:
        colors = generate_color_set(len(materials))
        BakeMaterialManager(
            mat=mat,
            bake_settings=settings,
            image_name=image.name,
            mat_id_color=colors[list(materials).index(mat)],
        )

        tree = mat.node_tree
        node_name = MaterialNodeNames.BAKE_TEXTURE
        bake_texture_node = tree.nodes.get(node_name)
        # bake_texture_node.image = image
        bake_texture_node.select = True
        tree.nodes.active = bake_texture_node


@dataclass(kw_only=True)
class BakeManager:
    """Manages scene, materials setup and Blender's bake operator."""

    context: b_t.Context
    objects: BakeObjects
    settings: BakeSettings
    image: b_t.Image
    clear_image: bool
    keep_scene: bool

    __running: bool = field(init=False, default=False)
    __og_scene: b_t.Scene = field(init=False)
    __materials: Sequence[b_t.Material] = field(init=False)

    @classmethod
    def is_running(cls) -> bool:
        """Return whether the instance of class is already active."""
        return cls.__running

    @classmethod
    def __set_running(cls, state: bool) -> None:
        cls.__running = state

    def on_execute(self) -> None:
        """Call handler from Operator's execute().

        Prepare baking scene and run bake Operator.
        """
        if self.is_running():
            raise AddonException(f"{type(self).__name__!r} already running.")
        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            raise AddonException("Blender OBJECT_BAKE job already running.")

        if self.context.mode != _EDITOR_MODE:
            bpy.ops.object.mode_set(mode=_EDITOR_MODE)

        self._save_user_settings()

        try:
            bake_result = self._unsafe_execute()
        except Exception:
            log_err("Failed to start baking, trying to clean up", with_tb=True)
            self.cleanup()
            raise

        if bake_result != {BlenderOperatorReturnType.RUNNING_MODAL}:
            self.cleanup()
            raise AddonException(
                "Failed to start baking. Wrong return type from object.bake operator.",
                bake_result,
            )

    def _unsafe_execute(self) -> set[BlenderOperatorReturnType]:
        self.__set_running(True)

        self.context.window.cursor_set("WAIT")

        get_props_wm(self.context).settings_scene = self.context.scene
        self.context.window.scene = _BakingScene.prepare(bake_settings=self.settings)

        # NOTE: Updating depsgraph to avoid random exception about
        # "writing ID in wrong context"
        self.context.view_layer.depsgraph.update()  # type: ignore[no-untyped-call]

        self._set_up_objects()

        self.__materials = tuple(get_objects_materials(self.objects.selected))
        _materials_cleanup(self.__materials)
        _materials_setup(self.__materials, self.settings, self.image)

        # TODO: implement uv_layer selection
        bake_result = call_bake_op(self.settings, use_clear=self.clear_image)
        return bake_result

    def on_modal(self) -> None:
        """Call handler from Operator's modal()."""
        if not self.is_running():
            # TODO: should we raise exception here?
            return
        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            return

        self.cleanup()

    def cleanup(self) -> None:
        """Clean up and restore user settings."""
        self._restore_user_settings()

        _materials_cleanup(self.__materials)

        _BakingScene.cleanup(keep_scene=self.keep_scene)

        self.__set_running(False)

    def cancel(self) -> None:
        """Cancel bake and cleanup."""
        self.cleanup()

    def _save_user_settings(self) -> None:
        self.__og_scene = self.context.window.scene

    def _restore_user_settings(self) -> None:
        self.context.window.scene = self.__og_scene
        get_props_wm(self.context).settings_scene = None
        self.context.window.cursor_set("DEFAULT")

    def _set_up_objects(self) -> None:
        for b_obj in self.context.selected_objects:
            b_obj.select_set(False)

        for b_obj in self.objects.selected:
            bake_coll = _BakingScene.get_bake_collection()
            bake_coll.objects.link(b_obj)

            b_obj.hide_set(False)
            b_obj.hide_render = False
            b_obj.hide_viewport = False
            b_obj.select_set(True)

        self.context.view_layer.objects.active = self.objects.active


class _BakingScene:
    __initialized: bool = False

    @classmethod
    def remove(cls) -> None:
        """Remove baking scenes."""
        for scene in bpy.data.scenes[:]:
            if scene.name.startswith(TMP_SCENE_NAME):
                bpy.data.scenes.remove(scene)

        cls.__initialized = False

    @classmethod
    def cleanup(cls, keep_scene: bool = True) -> None:
        """Clean up baking scene."""
        if not keep_scene:
            cls.remove()

        bake_coll = bpy.data.collections.get(BAKE_COLLECTION_NAME)
        if bake_coll is None:
            return
        for b_obj in bake_coll.objects[:]:
            bake_coll.objects.unlink(b_obj)
        bpy.data.collections.remove(bake_coll)

    @classmethod
    def create(cls, *, settings: BakeSettings) -> b_t.Scene:
        """Create and setup new baking scene."""
        log("Creating new scene")
        sc = bpy.data.scenes.new(TMP_SCENE_NAME)

        sc.cycles.device = "GPU"
        sc.cycles.samples = settings.samples
        sc.cycles.use_denoising = settings.use_denoising

        sc.render.use_lock_interface = True
        # NOTE: There is a weird hardlock when we setting engine to CYCLES
        sc.render.engine = _RENDER_ENGINE
        sc.render.bake.use_pass_direct = False
        sc.render.bake.use_pass_indirect = False
        sc.render.bake.use_pass_color = True

        cls.__initialized = True

        return sc

    @classmethod
    def prepare(
        cls,
        *,
        bake_settings: BakeSettings,
    ) -> b_t.Scene:
        """Prepare and fill up scene.

        Creates scene, collection and fills it with selected objects.
        """
        cls.cleanup(cls.__initialized)
        scene = bpy.data.scenes.get(TMP_SCENE_NAME)
        if not scene:
            scene = cls.create(settings=bake_settings)

        bake_coll = bpy.data.collections.new(BAKE_COLLECTION_NAME)
        scene.collection.children.link(bake_coll)

        return scene

    @staticmethod
    def get_bake_collection() -> b_t.Collection:
        """Return a Collection dedicated to baked meshes."""
        return bpy.data.collections.get(BAKE_COLLECTION_NAME)
