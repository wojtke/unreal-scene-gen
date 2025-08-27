import os
import sys
import importlib
import time
import unreal
import random
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import assets
import utils
import camera
import mesh_actor
import serialize

importlib.invalidate_caches()
importlib.reload(camera)
importlib.reload(utils)
importlib.reload(mesh_actor)
importlib.reload(assets)
importlib.reload(serialize)

AX, AY, AZ = 67170.0, 40950.0, -36400.0

OUTPUT_PATH = "C:/Users/woj/unreal_scripts/out/" + datetime.now().strftime('%y%m%d-%H%M%S')
os.makedirs(OUTPUT_PATH)

def schedule(cam, objects, gap=1.0):
    for i in range(100):
        for o in objects:
            rot = unreal.Rotator(0, 0, random.uniform(0.0, 360.0))
            pos = utils.sample_pos((AX, AY, AZ), std_xy=500)
            o.move_to(pos, rot)
        camera_pos = utils.sample_pos((AX, AY, AZ+1000), std_xy=1200, std_z=600)
        cam.move_to(camera_pos)
        cam.look_at_many([o.actor for o in objects])
        cam.take_screenshot(out_name=f"{OUTPUT_PATH}/img_{i:04d}.jpg", delay=0.1) 

        params = serialize.snapshot_params([o.actor for o in objects], cam.actor)
        json.dump(params, open(f"{OUTPUT_PATH}/params_{i:04d}.json","w"), indent=2, ensure_ascii=False)

        t0 = time.time()
        while time.time() - t0 < gap:
            yield None

if __name__ == "__main__":
    cube = mesh_actor.MeshActor(assets.CUBE_PATH).set_material(assets.BASIC_MTL_PATH)
    rock = mesh_actor.MeshActor(assets.ROCK_PATH)
    truck = mesh_actor.MeshActor(assets.TRUCK_PATH)
    
    cam = camera.RenderCineCamera()

    pt = utils.PyTick()
    pt.schedule.append(schedule(cam, [cube, rock, truck]))
    # utils.destroy_by_tag(tag="BATCH_TMP")

