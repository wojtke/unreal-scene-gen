# mesh_actor.py (UE 5.4)
import unreal
from typing import Optional

editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

class MeshActor:
   
    _instances: list["MeshActor"] = []

    def __init__(self,
                 mesh_path: str,
                 loc: unreal.Vector = None,
                 rot: unreal.Rotator = None,
                 label: Optional[str] = None,
                 scale: Optional[unreal.Vector] = None):
        mesh = unreal.load_object(None, mesh_path)
        if not mesh:
            raise RuntimeError(f"Failed to load StaticMesh: {mesh_path}")

        if loc is None:
            loc = unreal.Vector(0,0,0)
        if rot is None:
            rot = unreal.Rotator(0,0,0)

        self.actor: unreal.StaticMeshActor = editor.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        self.actor.tags = [unreal.Name("BATCH_TMP")]
        self.actor.static_mesh_component.set_static_mesh(mesh)
        if scale is not None:
            self.actor.set_actor_scale3d(scale)
        if label:
            self.actor.set_actor_label(label, True)

        MeshActor._instances.append(self)

    def _assert_alive(self):
        if self.actor is None:
            raise RuntimeError("MeshActor was destroyed")
        if not unreal.SystemLibrary.is_valid(self.actor): 
            raise RuntimeError("MeshActor is not valid (pending kill)")
        

    def move_to(self, loc: unreal.Vector, rot: unreal.Rotator) -> "MeshActor":
        self._assert_alive()
        if rot is None:
            rot = self.actor.get_actor_rotation()
        self.actor.set_actor_location_and_rotation(loc, rot, sweep=False, teleport=True)
        return self

    def set_material(self, mat_path: str, slot: int = 0) -> "MeshActor":
        self._assert_alive()
        mtl = unreal.load_object(None, mat_path)
        if not mtl:
            raise RuntimeError(f"Failed to load Material: {mat_path}")
        self.actor.static_mesh_component.set_material(slot, mtl)

        return self

    def destroy(self) -> None:
        unreal.EditorLevelLibrary.destroy_actor(self.actor)
        self.actor = None
        # remove from registry if present
        try:
            MeshActor._instances.remove(self)
        except ValueError:
            pass

    @classmethod
    def destroy_all(cls) -> None:
        for inst in list(cls._instances):
            if inst.actor and not inst.actor.is_pending_kill():
                unreal.EditorLevelLibrary.destroy_actor(inst.actor)
            inst.actor = None
        cls._instances.clear()
