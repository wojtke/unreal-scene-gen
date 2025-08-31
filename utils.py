import unreal 
import random
from typing import Tuple

from collections import deque
from collections.abc import Iterable


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


def destroy_by_tag(tag="SCRIPT_CREATED"):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if any(str(t) == tag for t in actor.tags):
            unreal.EditorLevelLibrary.destroy_actor(actor)