# mesh_actor.py (UE 5.4)
import unreal
import math
from typing import Optional

editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

class MeshActor:
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
        self.actor.tags = [unreal.Name("SCRIPT_GENERATED")]
        self.actor.static_mesh_component.set_static_mesh(mesh)
        if scale is not None:
            self.actor.set_actor_scale3d(scale)
        if label:
            self.actor.set_actor_label(label, True)

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

    def overlaps(self, other: "MeshActor", padding: float = 0.0) -> bool:
        """
        Return True if this actor's world-space AABB overlaps with another's.
        padding expands both boxes (in Unreal units).
        """
        self._assert_alive()
        other._assert_alive()

        # Get (origin, extent) for both actors
        a_origin, a_extent = self.actor.get_actor_bounds(False)
        b_origin, b_extent = other.actor.get_actor_bounds(False)

        # Convert to min/max corners
        a_min = unreal.Vector(a_origin.x - a_extent.x, a_origin.y - a_extent.y, a_origin.z - a_extent.z)
        a_max = unreal.Vector(a_origin.x + a_extent.x, a_origin.y + a_extent.y, a_origin.z + a_extent.z)
        b_min = unreal.Vector(b_origin.x - b_extent.x, b_origin.y - b_extent.y, b_origin.z - b_extent.z)
        b_max = unreal.Vector(b_origin.x + b_extent.x, b_origin.y + b_extent.y, b_origin.z + b_extent.z)

        p = padding
        return (
            (a_min.x <= b_max.x + p) and (a_max.x >= b_min.x - p) and
            (a_min.y <= b_max.y + p) and (a_max.y >= b_min.y - p) and
            (a_min.z <= b_max.z + p) and (a_max.z >= b_min.z - p)
        )

    def distance_to(self, other: "MeshActor") -> float:
        """
        Euclidean distance between actor pivots (world locations).
        """
        self._assert_alive()
        other._assert_alive()
        loc_a = self.actor.get_actor_location()
        loc_b = other.actor.get_actor_location()
        return loc_a.distance(loc_b)

    def aabb_distance_to(self, other: "MeshActor") -> float:
        """
        Shortest distance between world-space AABBs of two actors.
        Returns 0.0 if they overlap.
        """
        self._assert_alive()
        other._assert_alive()

        # Get bounds (origin, extent)
        a_origin, a_extent = self.actor.get_actor_bounds(False)
        b_origin, b_extent = other.actor.get_actor_bounds(False)

        # Min/max corners
        a_min = unreal.Vector(a_origin.x - a_extent.x, a_origin.y - a_extent.y, a_origin.z - a_extent.z)
        a_max = unreal.Vector(a_origin.x + a_extent.x, a_origin.y + a_extent.y, a_origin.z + a_extent.z)
        b_min = unreal.Vector(b_origin.x - b_extent.x, b_origin.y - b_extent.y, b_origin.z - b_extent.z)
        b_max = unreal.Vector(b_origin.x + b_extent.x, b_origin.y + b_extent.y, b_origin.z + b_extent.z)

        # Compute gap per axis (0 if overlapping)
        dx = max(0.0, max(b_min.x - a_max.x, a_min.x - b_max.x))
        dy = max(0.0, max(b_min.y - a_max.y, a_min.y - b_max.y))
        dz = max(0.0, max(b_min.z - a_max.z, a_min.z - b_max.z))

        return math.sqrt(dx*dx + dy*dy + dz*dz)
