# Plain note: writes a Material Maker graph (.ptex) for the brick wall where the LAYOUT comes from a fitted description file
# (brick_layout.json: every brick's left/top/right/bottom and average colour, found by analysis/fit_brick_layout.py) and everything else
# (soot, chips, mortar grain, painted look) comes from ordinary Material Maker library nodes.
# How the description gets in: one "Custom Shader" node whose code holds the brick list as constant arrays (the 'global' GLSL text), and
# three outputs: distance to the nearest brick edge (positive inside a brick), the fitted brick colour, and a random grey per brick.
# Usage: python3 -I make_brick_fitted_graph.py LAYOUT.json OUT.ptex [--flip-y] [--no-wear] [--seed N]
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptex_builder import Graph, gradient, colour

layout_path, out = sys.argv[1], sys.argv[2]
FLIP_Y = '--flip-y' in sys.argv
WEAR = '--no-wear' not in sys.argv
LITE = '--lite' in sys.argv   # blotches and chips only (no big soot patches): the fitted per-brick colour already contains the soot
seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 1
desc = json.load(open(layout_path))
bricks = desc['bricks']
N = len(bricks)

# ---- 1. the GLSL text with the brick list ---------------------------------------------------------------------------
rects = ', '.join('vec4(%.5f, %.5f, %.5f, %.5f)' % (b['x0'], b['y0'], b['x1'], b['y1']) for b in bricks)
cols = ', '.join('vec3(%.4f, %.4f, %.4f)' % tuple(b['rgb']) for b in bricks)
glsl_global = f'''const int BRICK_COUNT = {N};
const vec4 BRICK_RECT[{N}] = vec4[{N}]({rects});
const vec3 BRICK_RGB[{N}] = vec3[{N}]({cols});
const float BRICK_ROUND = 0.012;

// returns vec4(distance to nearest brick edge (positive inside the brick), brick index, 0, 0); looks at the tile and its 8 neighbours so bricks wrap round the edges
vec4 fitted_brick_lookup(vec2 uv) {{
	{'uv.y = 1.0 - uv.y;' if FLIP_Y else ''}
	float best = -1.0;
	float best_index = 0.0;
	for (int i = 0; i < BRICK_COUNT; i++) {{
		vec4 r = BRICK_RECT[i];
		vec2 centre = 0.5 * (r.xy + r.zw);
		vec2 half_size = 0.5 * (r.zw - r.xy);
		for (int sx = -1; sx <= 1; sx++) {{
			for (int sy = -1; sy <= 1; sy++) {{
				vec2 p = uv - centre - vec2(float(sx), float(sy));
				vec2 q = abs(p) - half_size + vec2(BRICK_ROUND);
				float d = -(length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - BRICK_ROUND);
				if (d > best) {{
					best = d;
					best_index = float(i);
				}}
			}}
		}}
	}}
	return vec4(best, best_index, 0.0, 0.0);
}}

vec3 fitted_brick_colour(vec2 uv) {{
	vec4 l = fitted_brick_lookup(uv);
	return BRICK_RGB[int(l.y)];
}}

float fitted_brick_grey(vec2 uv) {{
	vec4 l = fitted_brick_lookup(uv);
	return fract(sin(l.y * 12.9898 + 4.1414) * 43758.5453);
}}
'''

g = Graph()
shader = g.add('shader', 'FittedBricks', {}, seed=seed)
# replace the (empty) shader node with a full definition
node = g.nodes[-1]
node['shader_model'] = {
    'name': 'Fitted bricks', 'code': '', 'instance': '', 'global': glsl_global, 'inputs': [], 'parameters': [],
    'outputs': [
        {'f': 'fitted_brick_lookup($uv).x', 'type': 'f', 'shortdesc': 'Distance inside brick'},
        {'rgb': 'fitted_brick_colour($uv)', 'type': 'rgb', 'shortdesc': 'Fitted brick colour'},
        {'f': 'fitted_brick_grey($uv)', 'type': 'f', 'shortdesc': 'Random grey per brick'},
    ]}

# ---- 2. masks from the distance --------------------------------------------------------------------------------------
# distance is in tile fractions: 0.0016 = 2 px at 1254 px.  body mask: 1 inside a brick, soft 1.5 px edge
body = g.add('colorize', 'BodyMask', {'gradient': gradient([(0.0, (0, 0, 0)), (0.0012, (1, 1, 1))])})
g.connect(shader, 0, body, 0)
# dark outline: a thin line just INSIDE the brick edge (0 .. 0.004)
ring = g.add('colorize', 'OutlineMask', {'gradient': gradient([(0.0, (0, 0, 0)), (0.0008, (1, 1, 1)), (0.0035, (1, 1, 1)), (0.0075, (0, 0, 0))])})
g.connect(shader, 0, ring, 0)

# ---- 3. wear layers (ordinary library nodes) -----------------------------------------------------------------------------
brick_col = '__fitted'
cur = shader   # node whose output 1 is the fitted colour
cur_port = 1
if WEAR:
    blot = g.add('perlin', 'Blotches', {'scale_x': 12, 'scale_y': 14, 'iterations': 6, 'persistence': 0.6}, seed=seed + 21)
    blot_col = g.add('colorize', 'BlotchColour', {'gradient': gradient([(0.0, (0.78, 0.66, 0.60)), (0.5, (1.0, 1.0, 1.0)), (1.0, (1.25, 1.18, 1.10))])})
    g.connect(blot, 0, blot_col, 0)
    b1 = g.add('blend2', 'BrickBlotched', {'blend_type1': 2, 'amount1': 1.0})
    g.connect(cur, cur_port, b1, 0)
    g.connect(blot_col, 0, b1, 1)
    # soot
    b2 = b1
    if not LITE:
        streak = g.add('noise_anisotropic', 'Streaks', {'scale_x': 10, 'scale_y': 1.5, 'smoothness': 1, 'interpolation': 1}, seed=seed + 31)
        soot_big = g.add('perlin', 'SootAreas', {'scale_x': 5, 'scale_y': 5, 'iterations': 6, 'persistence': 0.65}, seed=seed + 32)
        soot_mul = g.add('blend2', 'SootMix', {'blend_type1': 2, 'amount1': 1.0})
        g.connect(streak, 0, soot_mul, 0)
        g.connect(soot_big, 0, soot_mul, 1)
        soot_mask = g.add('colorize', 'SootThreshold', {'gradient': gradient([(0.06, (0.95, 0.95, 0.95)), (0.26, (0, 0, 0))])})
        g.connect(soot_mul, 0, soot_mask, 0)
        soot_col = g.add('colorize', 'SootColour', {'gradient': gradient([(0.0, (0.08, 0.06, 0.05)), (1.0, (0.2, 0.12, 0.1))])})
        g.connect(soot_mul, 0, soot_col, 0)
        b2 = g.add('blend2', 'BrickSooty', {'blend_type1': 0, 'amount1': 0.85})
        g.connect(b1, 0, b2, 0)
        g.connect(soot_col, 0, b2, 1)
        g.connect(soot_mask, 0, b2, 2)
    # chips
    chip_noise = g.add('fbm4', 'ChipNoise', {'noise': 0, 'scale_x': 14, 'scale_y': 14, 'folds': 0, 'iterations': 5, 'persistence': 0.6, 'offset': 0}, seed=seed + 41)
    chip_mask = g.add('colorize', 'ChipThreshold', {'gradient': gradient([(0.68, (0, 0, 0)), (0.73, (1, 1, 1))])})
    g.connect(chip_noise, 0, chip_mask, 0)
    chip_col = g.add('colorize', 'ChipColour', {'gradient': gradient([(0.0, (0.62, 0.52, 0.40)), (1.0, (0.72, 0.60, 0.46))])})
    g.connect(chip_noise, 0, chip_col, 0)
    b3 = g.add('blend2', 'BrickChipped', {'blend_type1': 0, 'amount1': 0.9})
    g.connect(b2, 0, b3, 0)
    g.connect(chip_col, 0, b3, 1)
    g.connect(chip_mask, 0, b3, 2)
    cur, cur_port = b3, 0

# ---- 4. mortar, bricks over mortar, outline ------------------------------------------------------------------------------
mr, mg, mb = desc['mortar_rgb']
mort_noise = g.add('perlin', 'MortarNoise', {'scale_x': 16, 'scale_y': 16, 'iterations': 5, 'persistence': 0.6}, seed=seed + 51)
mort_col = g.add('colorize', 'MortarColour', {'gradient': gradient([(0.0, (mr * 0.75, mg * 0.75, mb * 0.75)), (0.6, (mr * 0.95, mg * 0.95, mb * 0.95)), (1.0, (mr * 1.15, mg * 1.15, mb * 1.15))])})
g.connect(mort_noise, 0, mort_col, 0)
wall = g.add('blend2', 'BricksOnMortar', {'blend_type1': 0, 'amount1': 1.0})
g.connect(mort_col, 0, wall, 0)
g.connect(cur, cur_port, wall, 1)
g.connect(body, 0, wall, 2)
dark = g.add('uniform', 'OutlineColour', {'color': colour((0.14, 0.09, 0.07))})
wall2 = g.add('blend2', 'WithOutline', {'blend_type1': 0, 'amount1': 0.75})
g.connect(wall, 0, wall2, 0)
g.connect(dark, 0, wall2, 1)
g.connect(ring, 0, wall2, 2)

# ---- 5. painted look, height from colour brightness, normal from height, roughness, occlusion ---------------------------------
paint = g.add('generalized_kuwahara', 'PaintedLook', {'buffer': 1, 'resolution': 11, 'size': 5})
g.connect(wall2, 0, paint, 0)
grey = g.add('greyscale', 'BrightnessOfColour', {'mode': 4})
g.connect(paint, 0, grey, 0)
height = g.add('colorize', 'Height', {'gradient': gradient([(0.0, (0.0, 0.0, 0.0)), (0.55, (0.8, 0.8, 0.8)), (1.0, (1.0, 1.0, 1.0))])})
g.connect(grey, 0, height, 0)
normal = g.add('normal_map2', 'NormalFromHeight', {'strength': 1.0, 'size': 11})
g.connect(height, 0, normal, 0)
rough = g.add('colorize', 'Roughness', {'gradient': gradient([(0.0, (0.95, 0.95, 0.95)), (0.001, (0.8, 0.8, 0.8)), (1.0, (0.78, 0.78, 0.78))])})
g.connect(body, 0, rough, 0)
ao = g.add('colorize', 'AmbientOcclusion', {'gradient': gradient([(0.0, (0.5, 0.5, 0.5)), (1.0, (1, 1, 1))])})
g.connect(body, 0, ao, 0)

mat = g.material('Material', metallic=0.0, depth_scale=0.5)
if '--probe' in sys.argv:
    probes = dict(item.split('=') for item in sys.argv[sys.argv.index('--probe') + 1].split(','))
    for port, spec in probes.items():
        node_name, _, nport = spec.partition(':')
        g.connect(node_name, int(nport or 0), mat, int(port))
else:
    g.connect(paint, 0, mat, 0)
    g.connect(rough, 0, mat, 2)
    g.connect(normal, 0, mat, 4)
    g.connect(ao, 0, mat, 5)
    g.connect(height, 0, mat, 6)
g.save(out)
print('wrote', out, 'with', len(g.nodes), 'nodes;', N, 'bricks in the description')
