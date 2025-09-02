import bpy

print(bpy.context.scene.pawsbkr)
assert bpy.context.scene.pawsbkr

ops_return = bpy.ops.pawsbkr.texture_set_bake(
    texture_set_id="e093af03-2ed1-4895-962a-564c4361809d"
)
print("ops_return", ops_return)
assert ops_return == {"RUNNING_MODAL"}

assert bpy.data.objects["Plane"].material_slots[0].material.name == "Material"


def wait_modal() -> float | None:
    if bpy.context.window.modal_operators.get(
        bpy.ops.pawsbkr.texture_set_bake.idname()
    ):
        print("TEST RUNNING")
        return 1.0

    print("BAKE FINISHED")

    assert (
        bpy.data.objects["Plane"].material_slots[0].material.name == "test_set_01_baked"
    )

    print("TEST FINISHED. QUITTING")

    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(wait_modal)
