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


def sample_obj_pos(objects):
    for o in objects:
        rot = unreal.Rotator(0, 0, random.uniform(0.0, 360.0))
        pos = unreal.Vector(
            random.gauss(AX, 500), 
            random.gauss(AY, 500), 
            random.gauss(AZ, 0) 
        )
        o.move_to(pos, rot)

    n = len(objects)
    for i in range(n):
        for j in range(i + 1, n):
            if objects[i].overlaps(objects[j]):
                return False
            if objects[i].distance_to(objects[j]) > 1000:
                return False
    return True


def sample_camera(cam, objects):
    camera_pos = unreal.Vector(
        random.uniform(AX-2500, AX+2500), 
        random.uniform(AY-2500, AY+2500), 
        random.uniform(AZ, AZ+1500)
    )
    cam.move_to(camera_pos)
    cam.look_at_many([o.actor for o in objects])

    cam_offset_angles = [cam.angle_to(o.actor) for o in objects]

    print(f"offset angles: {cam_offset_angles}")

    if max(cam_offset_angles) > min(cam.fov())-5:
        return False
    if max(cam_offset_angles) < 10:
        return False

    return True

def schedule(cam, objects, gap=1.5):
    for i in range(500):
        for j in range(10):
            good = sample_obj_pos(objects)
            print(f"Sampling obj pos iter={j}, good={good}")
            if good:
                break 

        for j in range(15):
            good = sample_camera(cam, objects)
            print(f"Sampling camera iter={j}, good={good}")
            if good:
                break 

        cam.take_screenshot(out_name=f"{OUTPUT_PATH}/img_{i:04d}.jpg", delay=0.2) 

        params = serialize.snapshot_params([o.actor for o in objects], cam.actor)
        json.dump(params, open(f"{OUTPUT_PATH}/params_{i:04d}.json","w"), indent=2, ensure_ascii=False)

        t0 = time.time()
        while time.time() - t0 < gap:
            yield None

if __name__ == "__main__":
    utils.destroy_by_tag(tag="SCRIPT_GENERATED")

    cube = mesh_actor.MeshActor(
        assets.CUBE_PATH, 
        label="Cube", 
        scale=unreal.Vector(1,1,2)
    ).set_material(assets.BASIC_MTL_PATH)

    rock = mesh_actor.MeshActor(assets.ROCK_PATH, label="Rock")
    truck = mesh_actor.MeshActor(assets.TRUCK_PATH, label="Truck")
    
    cam = camera.RenderCineCamera(label="RenderCamera")
    
    pt = utils.PyTick()
    pt.schedule.append(schedule(cam, [cube, rock, truck]))

