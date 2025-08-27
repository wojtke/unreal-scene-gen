# serialize.py (UE 5.4)
import math, unreal
from typing import Any, Dict, List, Union

def _is_valid(obj) -> bool:
    try:
        return obj is not None and unreal.SystemLibrary.is_valid(obj)
    except Exception:
        return obj is not None

def _vec(v: unreal.Vector) -> Dict[str, float]:
    return {"x": float(v.x), "y": float(v.y), "z": float(v.z)}

def _rot(r: unreal.Rotator) -> Dict[str, float]:
    return {"pitch": float(r.pitch), "yaw": float(r.yaw), "roll": float(r.roll)}

def _camera_intrinsics(cam: unreal.CineCameraActor) -> Dict[str, Any]:
    comp: unreal.CineCameraComponent = cam.get_cine_camera_component()
    fb = comp.get_editor_property("filmback")
    sensor_w = float(fb.sensor_width)
    sensor_h = float(fb.sensor_height)
    focal    = float(comp.get_editor_property("current_focal_length"))
    aperture = float(comp.get_editor_property("current_aperture"))

    hfov = math.degrees(2.0 * math.atan(0.5 * sensor_w / focal)) if focal > 0 else 0.0
    vfov = math.degrees(2.0 * math.atan(0.5 * sensor_h / focal)) if focal > 0 else 0.0

    fs = comp.get_editor_property("focus_settings")
    return {
        "sensor_width_mm": sensor_w,
        "sensor_height_mm": sensor_h,
        "focal_length_mm": focal,
        "aperture_f": aperture,
        "hfov_deg": hfov,
        "vfov_deg": vfov,
        "focus": {
            "method": str(getattr(fs, "focus_method", "")).split(".")[-1],
            "manual_distance": float(getattr(fs, "manual_focus_distance", 0.0)),
        },
    }

def snapshot_params(actors: List[Any], camera: Any) -> Dict[str, Any]:
    # accept wrappers or raw actors
    cam_actor = getattr(camera, "actor", getattr(camera, "get_actor", lambda: camera)())
    if not _is_valid(cam_actor):
        raise RuntimeError("Camera actor is invalid")

    data: Dict[str, Any] = {
        "camera": {
            "label": cam_actor.get_actor_label(),
            "path": cam_actor.get_path_name(),
            "location": _vec(cam_actor.get_actor_location()),
            "rotation": _rot(cam_actor.get_actor_rotation()),
            "intrinsics": _camera_intrinsics(cam_actor),
        },
        "actors": {}
    }

    for a in actors:
        act = getattr(a, "actor", a)
        if not _is_valid(act):
            continue
        key = act.get_path_name()
        data["actors"][key] = {
            "label": act.get_actor_label(),
            "location": _vec(act.get_actor_location()),
            "rotation": _rot(act.get_actor_rotation()),
        }

    return data
