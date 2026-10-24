"""What this does: makes a "clean plate" of a painting for SAM 3D objects: projects each SAM 3D model
into the painting (with the layout and lens found by fit_layout.py), draws its outline as a mask,
then paints the objects out of the painting and out of its depth picture (filling from the
surroundings), so the 3D models can stand on the ground instead of in their own painted copies.
Writes the masks, the clean painting (.jpg) and clean depth (.png), and a check picture.
Two steps, because Blender's Python has no OpenCV and the system Python has no Blender:
  blender-env/bin/python make_clean_plate.py masks METADATA.json GLB_FOLDER PAINTING.jpg DEPTH.png OUT_FOLDER NAME
  python3 -I make_clean_plate.py plate METADATA.json GLB_FOLDER PAINTING.jpg DEPTH.png OUT_FOLDER NAME"""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

step, meta_path, glb_folder, painting_path, depth_path, out, name = sys.argv[1:8]
TAN_X = 0.300                      # SAM 3D's lens, found by fit_layout.py
os.makedirs(out, exist_ok=True)
meta = json.load(open(meta_path))['objects']
painting = Image.open(painting_path).convert('RGB'); W, H = painting.size
TAN_Y = TAN_X * H / W

def quat_wxyz(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
TURN_X90 = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])

if step == 'masks':
  import bpy
  for k, path in enumerate(sorted(glob.glob(glb_folder + '/object-*.glb'))):
      bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
      bpy.ops.import_scene.gltf(filepath=path)
      o = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
      m = np.array(o.matrix_world)
      blender = np.array([(m @ np.array([*p.co, 1.0]))[:3] for p in o.data.vertices])
      gltf = np.stack([blender[:, 0], blender[:, 2], -blender[:, 1]], 1)
      R = quat_wxyz(meta[k]['rotation'][0]).T                       # the fit: w first, inverse
      p = (R @ (TURN_X90 @ gltf.T) * meta[k]['scale'][0][0]).T + np.array(meta[k]['translation'][0])
      u = (0.5 - 0.5 * (p[:, 0] / p[:, 2]) / TAN_X) * W            # SAM's x points left
      v = (0.5 - 0.5 * (p[:, 1] / p[:, 2]) / TAN_Y) * H
      mask = Image.new('L', (W, H), 0); draw = ImageDraw.Draw(mask)
      o.data.calc_loop_triangles()
      for t in o.data.loop_triangles:
          draw.polygon([(u[i], v[i]) for i in t.vertices], fill=255)
      mask.save(f'{out}/mask-{k + 1}.png')

  sys.exit(0)

import cv2
masks = [np.array(Image.open(f)) > 0 for f in sorted(glob.glob(f'{out}/mask-[0-9]*.png'))]
union = np.any(masks, axis=0).astype(np.uint8) * 255
union = cv2.dilate(union, np.ones((25, 25), np.uint8))          # a margin, so no painted edge is left
cv2.imwrite(f'{out}/mask-all.png', union)
picture = cv2.imread(painting_path)
clean = cv2.inpaint(picture, union, 18, cv2.INPAINT_TELEA)
cv2.imwrite(f'{out}/{name}.jpg', clean, [cv2.IMWRITE_JPEG_QUALITY, 93])
depth = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
depth_mask = cv2.resize(union, (depth.shape[1], depth.shape[0]), interpolation=cv2.INTER_NEAREST)
clean_depth = cv2.inpaint(depth, depth_mask, 18, cv2.INPAINT_TELEA)
cv2.imwrite(f'{out}/{name}-depth.png', clean_depth)
check = picture.copy(); check[union > 0] = (0.5 * check[union > 0] + [0, 0, 128]).astype(np.uint8)
sheet = np.concatenate([cv2.resize(x, (W // 3, H // 3)) for x in (check, clean, cv2.cvtColor(clean_depth, cv2.COLOR_GRAY2BGR) if clean_depth.shape[:2] == (H, W) else cv2.resize(cv2.cvtColor(clean_depth, cv2.COLOR_GRAY2BGR), (W, H)))], 1)
cv2.imwrite(f'{out}/check-clean-plate.jpg', sheet)
print('masks', [int(m.sum()) for m in masks], 'painting', (W, H), 'depth', depth.shape)
