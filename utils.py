import unreal 
import random
from typing import Tuple

from collections import deque
from collections.abc import Iterable

# AX, AY, AZ = 67170.0, 40950.0, -36400.0

# STD_XY = 1000.0   
# STD_Z  = 100.0    

def sample_pos(anchor, std_xy=500, std_z=0) -> unreal.Vector:
    ax, ay, az = anchor
    x = random.gauss(ax, std_xy)
    y = random.gauss(ay, std_xy)
    z = random.gauss(az, std_z) 
    return unreal.Vector(x, y, z)

def sample_rot() -> unreal.Rotator:
    return unreal.Rotator(0, 0, random.uniform(0.0, 360.0))

def sample_pos_rot() -> Tuple[unreal.Vector, unreal.Rotator]:
    return sample_pos(), sample_rot()

class PyTick():
    _delegate_handle = None
    _current = None
    schedule = None

    def __init__(self):
        self.schedule = deque()
        self._delegate_handle = unreal.register_slate_post_tick_callback(self._callback)

    def _callback(self, _):
        if self._current is None:
            if self.schedule:
                self._current = self.schedule.popleft()
            else:
                print('🏁 All jobs done.')
                unreal.unregister_slate_post_tick_callback(self._delegate_handle)
                return

        try:
            task = next(self._current)
            if task is not None and isinstance(task, Iterable):
                self.schedule.appendleft(self._current)
                self._current = task

        except StopIteration:
            self._current = None
        except Exception as e:
            self._current = None
            print(f"⚠️ Error during task: {e}")
            raise


def destroy_by_tag(tag="BATCH_TMP"):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if any(str(t) == tag for t in actor.tags):
            unreal.EditorLevelLibrary.destroy_actor(actor)