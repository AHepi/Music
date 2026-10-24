# What this does (plain words): re-measures the metal "derivation ceiling" for the normal map with NORMALISED reference normals
# (the way lib/pixel_compare.py measures), for the uploaded 8-bit height and for the height the generator's own rule makes from the
# reference colour, at strengths 4 to 7. Reads only the reference and the metal generator's derive_maps.py; writes nothing.
import json, sys
import numpy as np
import cv2
work = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
sys.path.insert(0, work + '/recipes/metal/generator')
import derive_maps as dm
ref_folder = work + '/reference/metal'
colour = cv2.imread(ref_folder + '/colour.png')[..., ::-1].astype(np.float64)
normal_reference = cv2.imread(ref_folder + '/normal.png')[..., ::-1].astype(np.float64) / 255.0 * 2 - 1
length = np.linalg.norm(normal_reference, axis=-1)
print('mean length of 8-bit reference normals', round(float(length.mean()), 4))
normal_reference_unit = normal_reference / length[..., None]
height_uploaded = cv2.imread(ref_folder + '/height_as_uploaded.png', cv2.IMREAD_UNCHANGED).astype(np.float64)
if height_uploaded.ndim == 3:
    height_uploaded = height_uploaded[..., 0]
height_uploaded = height_uploaded / (257.0 if height_uploaded.max() > 255 else 1.0) / 255.0
maps = json.load(open(work + '/recipes/metal/description/maps_rule.json'))
maps = maps.get('maps', maps)
height_predicted = dm.height_from_colour(colour, maps)
height_predicted = np.round(np.clip(height_predicted, 0, 1) * 255) / 255.0
def angle(height, strength, unit):
    n = dm.normal_from_height(height, strength) * 2 - 1
    n = n / np.linalg.norm(n, axis=-1, keepdims=True)
    reference = normal_reference_unit if unit else normal_reference
    return float(np.degrees(np.arccos(np.clip((n * reference).sum(-1), -1, 1))).mean())
base = maps['normal_strength']
print('strength in maps_rule.json', base)
for strength in (base * 4 / 5, base, base * 6 / 5, base * 7 / 5):
    print('strength', strength,
          'uploaded height: normalised', round(angle(height_uploaded, strength, True), 2), 'not normalised', round(angle(height_uploaded, strength, False), 2),
          '| predicted height: normalised', round(angle(height_predicted, strength, True), 2), 'not normalised', round(angle(height_predicted, strength, False), 2))
