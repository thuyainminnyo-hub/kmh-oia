# KMH_BAL_001 Blender Scene Master Builder v1.0
# Run from the extracted package root:
# blender --background --python scripts/build_blender_scene_master.py -- \
#   --asset-dir geometry --output KMH_BAL_001_MASTER_SCENE_v1.blend
#
# Requires Blender with glTF 2.0 import support.
# Creates an editable visual scene only. No physics or pyrotechnic design.

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def new_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def move_object(obj, target_collection):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    target_collection.objects.link(obj)


def import_meshes(filepath):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(filepath))
    added = set(bpy.context.scene.objects) - before
    return [obj for obj in added if obj.type == "MESH"]


def linked_duplicate(source, name, target_collection):
    obj = source.copy()
    obj.data = source.data
    obj.name = name
    target_collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    obj.hide_set(False)
    obj.hide_render = False
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_ortho_camera(name, location, target, collection, ortho_scale=2.8):
    camera_data = bpy.data.cameras.new(name + "_DATA")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = ortho_scale
    camera = bpy.data.objects.new(name, camera_data)
    collection.objects.link(camera)
    camera.location = location
    look_at(camera, target)
    camera["purpose"] = "QA projection only; not a measurement camera."
    return camera


def set_state(scene, base_collection, attached_collection, state):
    if state == "BASE-UNLOADED":
        base_collection.hide_viewport = False
        base_collection.hide_render = False
        attached_collection.hide_viewport = True
        attached_collection.hide_render = True
    elif state == "DISPLAYED-ATTACHED":
        base_collection.hide_viewport = True
        base_collection.hide_render = True
        attached_collection.hide_viewport = False
        attached_collection.hide_render = False
    else:
        raise ValueError("Unknown state: " + state)
    scene["active_state"] = state


def main():
    args = parse_args()
    asset_dir = Path(args.asset_dir).resolve()
    body_path = asset_dir / "KMH_BAL_001_BODY_BLOCKOUT_v1.glb"
    skirt_path = asset_dir / "KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb"

    if not body_path.is_file() or not skirt_path.is_file():
        raise FileNotFoundError("Both Geometry v1 GLBs must exist in --asset-dir.")

    # Clear scene objects and top-level child collections.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    for child in list(scene.collection.children):
        scene.collection.children.unlink(child)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    root = new_collection("KMH_BAL_001_MASTER", scene.collection)
    asset_library = new_collection("00_ASSET_LIBRARY_DO_NOT_EDIT", root)
    base_state = new_collection("01_STATE_BASE_UNLOADED", root)
    attached_state = new_collection("02_STATE_DISPLAYED_ATTACHED", root)
    artwork_root = new_collection("03_ARTWORK_LAYERS_EMPTY_UNTIL_MAPPED", root)
    attachment_root = new_collection("04_ATTACHMENT_REFERENCE_ONLY", root)
    reference_root = new_collection("05_REFERENCE_PHOTOS_AND_PROVENANCE", root)
    camera_root = new_collection("06_QA_CAMERAS", root)

    body_objects = import_meshes(body_path)
    skirt_objects = import_meshes(skirt_path)
    if len(body_objects) != 1 or len(skirt_objects) != 1:
        raise RuntimeError("Expected exactly one mesh object from each GLB.")

    body_master = body_objects[0]
    skirt_master = skirt_objects[0]
    body_master.name = "KMH_BAL_001_ENV_MASTER_V1"
    skirt_master.name = "KMH_BAL_001_SKIRT_MASTER_V1"
    move_object(body_master, asset_library)
    move_object(skirt_master, asset_library)

    for source in (body_master, skirt_master):
        source.hide_set(True)
        source.hide_render = True
        source["asset_role"] = "Preserved Geometry v1 source; do not edit."
        source["units"] = "Normalized arbitrary units; no physical scale."

    # State variants share the same two mesh datablocks.
    base_body = linked_duplicate(body_master, "BASE_UNLOADED__ENVELOPE", base_state)
    base_skirt = linked_duplicate(skirt_master, "BASE_UNLOADED__LOWER_SKIRT", base_state)
    attached_body = linked_duplicate(body_master, "DISPLAYED_ATTACHED__ENVELOPE", attached_state)
    attached_skirt = linked_duplicate(skirt_master, "DISPLAYED_ATTACHED__LOWER_SKIRT", attached_state)

    for obj, state in (
        (base_body, "BASE-UNLOADED"),
        (base_skirt, "BASE-UNLOADED"),
        (attached_body, "DISPLAYED-ATTACHED"),
        (attached_skirt, "DISPLAYED-ATTACHED"),
    ):
        obj["geometry_state"] = state
        obj["state_specific_deformation"] = "NOT_MODELED"

    base_state["state_id"] = "BASE-UNLOADED"
    base_state["description"] = "Envelope reference without the separate suspended Yan-Khwe."
    attached_state["state_id"] = "DISPLAYED-ATTACHED"
    attached_state["description"] = "Attached display reference; longer appearance is user-reported, not measured."
    attached_state["yan_khwe_asset_id"] = "KMH-BAL-001-ATT-001"
    attached_state["yan_khwe_status"] = "REFERENCE_ONLY_NOT_MODELED_NOT_POSITIONED"

    for zone in (
        "FRONT_BUDDHA_HALO",
        "REAR_LETTERING",
        "SIDE_NARRATIVE_ARTWORK",
        "LOWER_RADIAL_ORNAMENT",
        "COLOR_AND_SURFACE_PATTERNS",
    ):
        zone_collection = new_collection("ART_" + zone, artwork_root)
        zone_collection["mapping_status"] = "NOT_MAPPED"
        zone_collection["source_provenance_required"] = True

    attachment_root["asset_id"] = "KMH-BAL-001-ATT-001"
    attachment_root["name"] = "ယမ်းခွေ (Yan-Khwe)"
    attachment_root["status"] = "REFERENCE_ONLY_NOT_MODELED_NOT_POSITIONED"
    attachment_root["geometry_inference"] = "PROHIBITED"
    reference_root["capture_set_status"] = "NOT_CALIBRATED"
    reference_root["preserve_originals"] = True

    target = (0.0, 0.0, 0.5)
    front_camera = add_ortho_camera("QA_FRONT", (0.0, -4.0, 0.5), target, camera_root)
    add_ortho_camera("QA_SIDE", (4.0, 0.0, 0.5), target, camera_root)
    add_ortho_camera("QA_REAR", (0.0, 4.0, 0.5), target, camera_root)
    add_ortho_camera("QA_TOP", (0.0, 0.0, 4.0), target, camera_root)
    scene.camera = front_camera

    scene["project"] = "KMH Myanmar Balloon 3D Intelligence"
    scene["asset_id"] = "KMH-BAL-001"
    scene["scene_version"] = "1.0"
    scene["coordinate_system"] = "Z_UP"
    scene["physical_scale"] = "NOT_APPLIED"
    scene["geometry_v1_status"] = "PRESERVED"
    scene["geometry_v2_status"] = "HOLD"
    scene["production_status"] = "NOT_AUTHORIZED"
    set_state(scene, base_state, attached_state, "BASE-UNLOADED")

    bpy.ops.object.select_all(action="DESELECT")
    base_body.select_set(True)
    bpy.context.view_layer.objects.active = base_body

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print("Saved Blender scene:", output_path)


if __name__ == "__main__":
    main()
