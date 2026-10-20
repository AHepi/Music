# What this does: small checks of things web pages and manuals claim, each measured in Blender 5.2.2. Writes misc_checks.json.
#  1 what material.use_nodes = True prints in 5.2.2          2 Float Curve default ends (extrapolated or flat?)
#  3 Brick: is each brick a flat colour, and how many different colours show up?     4 Voronoi Normalize: value ranges per feature
#  5 Gabor 3D works / 2D ignores Z                           6 Shader to RGB inside Cycles (a toon-shading trick)
#  7 Noise "Color" output: are the 3 channels different noises?     8 Mapping vector types: what Location does to Vector and Normal
import os, sys, json, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
bh = pt.bh
OUT = os.path.dirname(os.path.abspath(__file__))
R = {}
D = 'ShaderNodeTex'

# 1 use_nodes ------------------------------------------------------------------------------------------------------
import warnings
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    m = bpy.data.materials.new('x'); m.use_nodes = True
    R['1_use_nodes_warnings_python'] = [str(c.message)[:200] for c in caught]
R['1_new_material_has_node_tree_without_use_nodes'] = bool(bpy.data.materials.new('y').node_tree)

# 2 float curve ends ----------------------------------------------------------------------------------------------
t = bpy.data.node_groups.new('q', 'ShaderNodeTree'); fc = t.nodes.new('ShaderNodeFloatCurve')
cm = fc.mapping; cur = cm.curves[0]
R['2_float_curve_default_extend'] = cm.extend
cur.points.new(0.5, 1.0); cm.update()
R['2_float_curve_evaluate'] = {str(x): round(cm.evaluate(cur, x), 3) for x in (-0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5)}
cm.extend = 'HORIZONTAL'; cm.update()
R['2_float_curve_evaluate_after_extend_HORIZONTAL'] = {str(x): round(cm.evaluate(cur, x), 3) for x in (-0.5, 1.5)}

# 3 brick -----------------------------------------------------------------------------------------------------------
def brick_body(w):
    b = w.add(D + 'Brick', 'b', x=0, offset=0.5)
    b.inputs['Color1'].default_value = (0, 0, 0, 1); b.inputs['Color2'].default_value = (1, 1, 1, 1); b.inputs['Mortar'].default_value = (0.5, 0.5, 0.5, 1)
    b.inputs['Scale'].default_value = 2.0; b.inputs['Mortar Size'].default_value = 0.03; b.inputs['Mortar Smooth'].default_value = 0.0; b.inputs['Bias'].default_value = 0.0
    w.link('in', 'Vector', 'b', 'Vector'); w.link('b', 'Color', 'out', 'Height')
a = pt.render_float(brick_body, 'Height', 400)
vals = np.round(a.ravel(), 2)
uniq, cnt = np.unique(vals, return_counts=True)
R['3_brick_colour_values'] = {'distinct values (rounded 0.01)': int(len(uniq)), 'share of pixels at mortar grey 0.5': round(float((np.abs(a - 0.5) < 0.005).mean()), 3),
                              'min': round(float(a.min()), 3), 'max': round(float(a.max()), 3)}
def brick_fac(w):
    b = w.add(D + 'Brick', 'b', x=0, offset=0.5); b.inputs['Scale'].default_value = 2.0; b.inputs['Mortar Size'].default_value = 0.03; b.inputs['Mortar Smooth'].default_value = 0.0
    w.link('in', 'Vector', 'b', 'Vector'); w.link('b', 'Factor', 'out', 'Height')
f = pt.render_float(brick_fac, 'Height', 400)
R['3_brick_factor'] = {'min': round(float(f.min()), 3), 'max': round(float(f.max()), 3), 'share mortar (=1)': round(float((f > 0.99).mean()), 3), 'share brick (=0)': round(float((f < 0.01).mean()), 3)}

# 4 voronoi normalize -----------------------------------------------------------------------------------------------
vr = {}
for feat, out in [('F1', 'Distance'), ('F2', 'Distance'), ('SMOOTH_F1', 'Distance'), ('DISTANCE_TO_EDGE', 'Distance'), ('N_SPHERE_RADIUS', 'Radius')]:
    for norm in (False, True):
        def body(w, feat=feat, out=out, norm=norm):
            v = w.add(D + 'Voronoi', 'v', x=0, feature=feat, normalize=norm, Scale=5.0); w.link('in', 'Vector', 'v', 'Vector'); w.link('v', out, 'out', 'Height')
        a = pt.render_float(body, 'Height', 120)
        vr[f'{feat} normalize={norm}'] = [round(float(a.min()), 3), round(float(a.mean()), 3), round(float(a.max()), 3)]
R['4_voronoi_range_min_mean_max'] = vr

# 5 gabor ---------------------------------------------------------------------------------------------------------
def gabor_point(mode, vec):
    def body(w):
        w.add('ShaderNodeCombineXYZ', 'xyz', x=-1, X=vec[0], Y=vec[1], Z=vec[2])
        g = w.add(D + 'Gabor', 'g', x=0, gabor_type=mode); g.inputs['Scale'].default_value = 3.0
        w.link('xyz', 'Vector', 'g', 0); w.link('g', 'Value', 'out', 'Height')
    return round(float(pt.render_float(body, 'Height', 4).mean()), 4)
R['5_gabor'] = {'2D z=0.1': gabor_point('2D', (0.31, 0.77, 0.1)), '2D z=9': gabor_point('2D', (0.31, 0.77, 9.0)), '3D z=0.1': gabor_point('3D', (0.31, 0.77, 0.1)), '3D z=9': gabor_point('3D', (0.31, 0.77, 9.0))}

# 6 shader to rgb in cycles -------------------------------------------------------------------------------------------
scene, tile = bh.new_bake_scene(64)
scene.cycles.samples = 8; scene.cycles.max_bounces = 2
ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 3
sun = bpy.data.objects.new('sun', ld); scene.collection.objects.link(sun); sun.rotation_euler = (0.3, 0.2, 0)
mm = bpy.data.materials.new('stor'); mm.use_nodes = True; mm.node_tree.nodes.clear()
import recipe_tools as rt
w = rt.NodeWriter(mm.node_tree)
w.add('ShaderNodeBsdfDiffuse', 'diff', x=0)
w.add('ShaderNodeShaderToRGB', 's2r', x=1); w.link('diff', 'BSDF', 's2r', 'Shader')
w.add('ShaderNodeEmission', 'em', x=2); w.link('s2r', 'Color', 'em', 'Color'); w.add('ShaderNodeOutputMaterial', 'out', x=3); w.link('em', 'Emission', 'out', 'Surface')
tile.data.materials.append(mm)
scene.render.filepath = os.path.join(OUT, '_s2r.exr'); scene.render.image_settings.file_format = 'OPEN_EXR'; scene.view_settings.view_transform = 'Raw'
log = io.StringIO()
bpy.ops.render.render(write_still=True)
im = bpy.data.images.load(scene.render.filepath); px = np.array(im.pixels[:]).reshape(-1, 4)
R['6_shader_to_rgb_in_cycles_mean_pixel'] = [round(float(x), 4) for x in px[:, :3].mean(axis=0)]

# 7 noise colour channels ---------------------------------------------------------------------------------------------
def nc(w):
    n = w.add(D + 'Noise', 'n', x=0, Scale=5.0); w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Color', 'out', 'Colour')
c = pt.render_float(nc, 'Colour', 96)
R['7_noise_colour_channel_correlations_RG_RB_GB'] = [round(float(np.corrcoef(c[..., i].ravel(), c[..., j].ravel())[0, 1]), 3) for i, j in ((0, 1), (0, 2), (1, 2))]
def nf(w):
    n = w.add(D + 'Noise', 'n', x=0, Scale=5.0); w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
f = pt.render_float(nf, 'Height', 96)
R['7_noise_Fac_vs_Color_channel_correlation'] = [round(float(np.corrcoef(c[..., i].ravel(), f.ravel())[0, 1]), 3) for i in range(3)]

# 8 mapping vector types -----------------------------------------------------------------------------------------------
def mp(vt, vec=(0.2, 0.4, 0.6)):
    def body(w):
        w.add('ShaderNodeCombineXYZ', 'xyz', x=-2, X=vec[0], Y=vec[1], Z=vec[2])
        m = w.add('ShaderNodeMapping', 'm', x=-1, vector_type=vt)
        m.inputs[1].default_value = (1.0, 2.0, 3.0); m.inputs[2].default_value = (0, 0, 0); m.inputs[3].default_value = (2.0, 2.0, 2.0)
        w.link('xyz', 'Vector', 'm', 'Vector')
        sep = w.add('ShaderNodeSeparateXYZ', 'sep', x=0); w.link('m', 'Vector', 'sep', 'Vector')
        cmb = w.add('ShaderNodeCombineColor', 'cc', x=1); w.link('sep', 'X', 'cc', 0); w.link('sep', 'Y', 'cc', 1); w.link('sep', 'Z', 'cc', 2)
        w.link('cc', 'Color', 'out', 'Colour')
    a = pt.render_float(body, 'Colour', 4)
    return [round(float(a[..., i].mean()), 3) for i in range(3)]
R['8_mapping_(vec 0.2,0.4,0.6; Location 1,2,3; Scale 2)'] = {vt: mp(vt) for vt in ('POINT', 'TEXTURE', 'VECTOR', 'NORMAL')}
json.dump(R, open(os.path.join(OUT, 'misc_checks.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
