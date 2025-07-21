from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

import bpy
from bpy import types as b_t

from .._helpers import log
from ..enums import BlenderJobType
from ..props import BakeSettings, get_props
from ..props_enums import BakeTextureType
from ..utils import AddonException
from ._utils import show_image_in_editor
from .bake_common import BakeObjects
from .bake_manager import BakeManager


class BakeJobState(Enum):
    # CREATED = auto()
    RUNNING = auto()
    CANCELED = auto()
    FINISHED = auto()


class BakeHandlerState(Enum):
    CREATED = auto()
    PRE = auto()
    CANCELED = auto()
    COMPLETE = auto()


@dataclass(kw_only=True)
class BakeJob:
    context: b_t.Context
    objects: BakeObjects
    settings: BakeSettings
    clear_image: bool
    scale_image: bool

    image_name: str
    image_path: str

    __image: b_t.Image = field(init=False)
    __manager: BakeManager = field(init=False)
    __handlers_state: BakeHandlerState = field(
        init=False, default=BakeHandlerState.CREATED
    )

    def __post_init__(self) -> None:
        self.__handlers = (
            (
                bpy.app.handlers.object_bake_pre,
                self.__cb_object_bake_factory(BakeHandlerState.PRE),
            ),
            (
                bpy.app.handlers.object_bake_cancel,
                self.__cb_object_bake_factory(BakeHandlerState.CANCELED),
            ),
            (
                bpy.app.handlers.object_bake_complete,
                self.__cb_object_bake_factory(BakeHandlerState.COMPLETE),
            ),
        )

    def on_execute(self) -> BakeJobState:
        """Call handler from Operator's execute()."""
        if bpy.app.is_job_running(BlenderJobType.OBJECT_BAKE):
            raise AddonException("Blender OBJECT_BAKE job already running.")
        if BakeManager.is_running():
            raise AddonException(
                f"Another instance of {BakeManager.__name__!r} already running."
            )

        self.__image = self.__image_prepare()
        show_image_in_editor(self.context, self.__image)

        self.__manager = BakeManager(
            context=self.context,
            objects=self.objects,
            settings=self.settings,
            image=self.__image,
            clear_image=self.clear_image,
            keep_scene=True,
        )

        for handler, cb in self.__handlers:
            handler.append(cb)

        try:
            self.__manager.on_execute()
        except AddonException:
            # TODO: parametrize for debug purposes
            self.__cleanup()
            raise

        return BakeJobState.RUNNING

    def on_modal(self) -> BakeJobState:
        """Call handler from Operator's modal()."""
        self.__manager.on_modal()
        if BakeManager.is_running():
            return BakeJobState.RUNNING

        if self.__handlers_state == BakeHandlerState.PRE:
            log("BakeManager is not running, but handler callback wasn't called")
            return BakeJobState.RUNNING

        if self.__handlers_state == BakeHandlerState.CANCELED:
            # TODO: check for BakeManager state or cleanup it?
            return BakeJobState.CANCELED

        if self.__handlers_state == BakeHandlerState.COMPLETE:
            if all(img.is_dirty for img in [self.__image]):
                self.__image_finalize()
                self.__cleanup()
                return BakeJobState.FINISHED

        self.__cleanup()
        raise AddonException(
            "Baking went wrong: Bake job not running but images appear to be unchanged"
        )

    def cancel(self) -> None:
        """Cancel running bake job and cleanup."""
        self.__manager.cancel()
        self.__cleanup()

    def __cb_object_bake_factory(
        self, state: BakeHandlerState
    ) -> Callable[[b_t.Object, Any], None]:
        def cb(b_obj: b_t.Object, _: Any) -> None:
            if b_obj is self.objects.active:
                self.__handlers_state = state

        return cb

    def __image_prepare(self) -> b_t.Image:
        img = bpy.data.images.get(self.image_name)

        if img is None and Path(bpy.path.abspath(self.image_path)).exists():
            img = bpy.data.images.load(self.image_path, check_existing=False)

        real_size = int(self.settings.size) * int(self.settings.sampling)
        if img is None:
            log("Creating new image")
            img = bpy.data.images.new(
                name=self.image_name,
                width=real_size,
                height=real_size,
                alpha=False,
                float_buffer=BakeTextureType[self.settings.type].is_float,
            )
            img.filepath = self.image_path
        else:
            log("Using existing image")
            # Convert both paths to absolute paths before comparison
            existing_path = bpy.path.abspath(img.filepath)
            expected_path = bpy.path.abspath(self.image_path)
            
            if bpy.path.native_pathsep(existing_path) != bpy.path.native_pathsep(expected_path):
                raise AddonException(
                    "Existing image has different filepath.",
                    {
                        "image": self.image_name,
                        "expected": bpy.path.native_pathsep(expected_path),
                        "got": bpy.path.native_pathsep(existing_path),
                    },
                )

            if self.clear_image:
                log("Creating clear image")
                blank_img = bpy.data.images.new(
                    name=self.image_name,
                    width=real_size,
                    height=real_size,
                    alpha=False,
                    float_buffer=BakeTextureType[self.settings.type].is_float,
                )
                blank_img.filepath = self.image_path
                blank_img.save(quality=0)
                bpy.data.images.remove(blank_img)

                img.reload()  # type: ignore[no-untyped-call]
            elif (
                img.size[0] != real_size
                or img.size[1] != real_size
                # or img.alpha_mode is not None
                or img.is_float != BakeTextureType[self.settings.type].is_float
            ):
                raise AddonException(
                    "Image already exist but its parameters doesn't match.",
                    {
                        "image": img,
                        "size": img.size,
                        "alpha_mode": img.alpha_mode,
                        "is_float": img.is_float,
                    },
                )

        img.colorspace_settings.name = BakeTextureType[self.settings.type].colorspace

        return img

    def __image_finalize(self) -> None:
        for img in (self.__image,):
            if self.scale_image and int(self.settings.sampling) > 1:
                img.scale(int(self.settings.size), int(self.settings.size))

            img.save(quality=0)

            if get_props(self.context).utils_settings.unlink_baked_image:
                bpy.data.images.remove(img)
            else:
                show_image_in_editor(self.context, img)

    def __cleanup(self) -> None:
        for handler, cb in self.__handlers:
            if cb in handler:
                handler.remove(cb)
