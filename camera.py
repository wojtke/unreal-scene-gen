# camera.py (UE 5.4) — minimal patch
import os, time, math, unreal
from typing import List

class RenderCineCamera:
    def __init__(self,
                 location: unreal.Vector = None,
                 rotation: unreal.Rotator= None,
                 sensor_mm: float = 50.0,
                 focal_length: float = 50.0,
                 aperture: float = 10.0,
                 focus_enabled: bool = False,
                 focus_distance: float = 4000.0):

        if location is None:
            location = unreal.Vector(0,0,0)
        if rotation is None:
            rotation = unreal.Rotator(0,0,0)
            
        self.cam: unreal.CineCameraActor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, location, rotation
        )
        self.cam.tags = [unreal.Name("BATCH_TMP")]
        self.comp: unreal.CineCameraComponent = self.cam.get_cine_camera_component()

        fb = self.comp.get_editor_property("filmback")
        fb.sensor_width = float(sensor_mm)
        fb.sensor_height = float(sensor_mm)
        self.comp.set_editor_property("filmback", fb)

        self.comp.set_editor_property("current_focal_length", float(focal_length))
        self.comp.set_editor_property("current_aperture", float(aperture))

        self._focus_enabled = False
        self.set_focus_enabled(focus_enabled, manual_distance=focus_distance)

        # keep roll at 0; pass teleport_physics flag
        rot = self.cam.get_actor_rotation()
        self.cam.set_actor_rotation(unreal.Rotator(rot.pitch, rot.yaw, 0.0), False)
        self._pending_tasks = []

    def move_to(self, location: unreal.Vector, rotation: unreal.Rotator=None):
        if rotation is None:
            rotation = self.cam.get_actor_rotation()
        self.cam.set_actor_location_and_rotation(location, rotation, sweep=False, teleport=True)

    def focus_at(self, target_actor: unreal.Actor):
        fs = self.comp.get_editor_property("focus_settings")
        fs.focus_method = unreal.CameraFocusMethod.TRACKING
        tfs = fs.tracking_focus_settings
        tfs.actor_to_track = target_actor
        fs.tracking_focus_settings = tfs
        self.comp.set_editor_property("focus_settings", fs)

    def look_at(self, target_actor: unreal.Actor):
        from_loc = self.cam.get_actor_location()
        to_loc   = target_actor.get_actor_location()
        look_rot = unreal.MathLibrary.find_look_at_rotation(from_loc, to_loc)

        self.cam.set_actor_rotation(look_rot, False)

        if self._focus_enabled:
            self.focus_at(target_actor)

    def look_at_many(self, target_actors: List[unreal.Actor]):
        pts = [a.get_actor_location() for a in target_actors]
        n = float(len(pts))
        center = unreal.Vector(
            sum(p.x for p in pts) / n,
            sum(p.y for p in pts) / n,
            sum(p.z for p in pts) / n,
        )
        from_loc = self.cam.get_actor_location()
        look_rot = unreal.MathLibrary.find_look_at_rotation(from_loc, center)
        self.cam.set_actor_rotation(look_rot, False)  

    def take_screenshot(self, out_name: str = "shot", res: tuple[int, int] = (2048, 2048), delay: float = 0.1) -> str:
        shots_dir = os.path.join(unreal.Paths.project_saved_dir(), "Screenshots", "Python")
        os.makedirs(shots_dir, exist_ok=True)
        out_path = os.path.join(shots_dir, f"{out_name}")
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            int(res[0]), int(res[1]), out_path, camera=self.cam,
            mask_enabled=False, capture_hdr=False, delay=delay, force_game_view=True
        )
        self._pending_tasks.append(task)  
        unreal.log(f"[camera] Requested screenshot -> {out_path}")
        return out_path

    def set_focus_enabled(self, enabled: bool, manual_distance: float | None = None):
        fs = self.comp.get_editor_property("focus_settings")
        try:
            fs.focus_method = unreal.CameraFocusMethod.DISABLE if not enabled else unreal.CameraFocusMethod.MANUAL
        except Exception:
            fs.focus_method = unreal.CameraFocusMethod.MANUAL
        if enabled and manual_distance is not None:
            fs.manual_focus_distance = float(manual_distance)
        self.comp.set_editor_property("focus_settings", fs)
        self._focus_enabled = bool(enabled)

    @property
    def actor(self) -> unreal.CineCameraActor:
        return self.cam
