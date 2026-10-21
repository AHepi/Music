# What this does (plain words): STUDY ONLY. Opens the saved Japanese courtyard IN MEMORY (never saves it) and tests, with small pictures, whether one
# generic "hook" can be put in front of EVERY weatherable material of the courtyard without changing the picture:
#   * a plain Principled material (numbers or wires)  -> a do-nothing group is spliced between whatever feeds each plug and the plug;
#   * the add-on's own stone / ceramic / timber shader groups (no Principled box on the surface) -> an ADAPTER first rebuilds the same Principled box
#     from the group's own outputs (Albedo, Roughness, Normal) and then the same splice is made;
#   * glow-only and see-through-leaf materials are skipped.
# It draws the courtyard before and after (Cycles, same seed, no noise cleaning) and measures the largest difference, then draws a flat colour map of the
# families the hook reaches. Pictures go next to OUT_PREFIX.
# Run: blender -b --disable-autoexec FILE --python c6_hook_test.py -- OUT_PREFIX [WIDTH] [SAMPLES] [control]
#   'control' makes the hook darken every colour by 2 % (a deliberate change) to prove that the comparison can see a change and that the hook really sits in the path of every weatherable material.
import json, re, sys, time
from collections import Counter, defaultdict
import bpy, numpy as np

args = sys.argv[sys.argv.index('--') + 1:]
PREFIX = args[0]; WIDTH = int(args[1]) if len(args) > 1 else 480; SAMPLES = int(args[2]) if len(args) > 2 else 16
scene = bpy.context.scene
T0 = time.time()
def say(t): print(f'[{time.time() - T0:6.1f}s] {t}', flush=True)

# ---------------------------------------------------------------- which materials belong to which family (by the objects that use them, instances included)
FAM = [('ground and earth', r'^(Astra / Courtyard receiving ground|Courtyard ground source)$'), ('moss and pebbles (add-on)', r'^Astra / (moss|pebbles) grouped'),
       ('raked gravel', r'^Raked gravel'), ('water', r'(water)$'), ('wood (planks, posts, beams, roof deck)', r'^(Astra / varied planks|Hall posts|Hall beams|Eave soffit|Shoji bars|Hall roof)'),
       ('plaster', r'^(Hall plaster|Back wall, (left|right)$|Right wall behind hall$)'), ('wall cap tiles', r' cap$'),
       ('roof tiles', r'^CT / Ceramic pan prototype$'), ('stone (add-on stones)', r'^(Stepping stone|Veranda step|Pond edge stone|Rock \d|Gravel rock|Lantern (base|post|gallery|firebox|cap)|Water basin|Bridge pier)'),
       ('plain stone (plinth)', r'^(Stone plinth|Lantern finial)$'), ('bamboo', r'^Bamboo'), ('bark', r'^(Maple|Pine) (trunk|branch|limb)'),
       ('leaves and needles', r'^(Maple leaves|Maple inner mass|Pine pads|Fallen leaves|Lily pads|Lotus)'), ('glow and backdrop', r'^(Shoji paper|Open room back|Lantern window glow|Hills,|Dark plain)')]
def fam_of(name):
    for f, rx in FAM:
        if re.search(rx, name): return f
    return 'other'
mat_fam = {}
for ob in bpy.data.objects:
    if ob.type not in ('MESH', 'CURVE'): continue
    for s in ob.material_slots:
        if s.material: mat_fam.setdefault(s.material.name, fam_of(ob.name))
roof = bpy.data.objects['Hall roof']
for nm in ('CT / Timber painterly surface', 'CT / Ceramic ridge host-local surface'): mat_fam.setdefault(nm, 'wood (planks, posts, beams, roof deck)' if 'Timber' in nm else 'roof tiles')
for m in bpy.data.materials:
    mat_fam.setdefault(m.name, 'unused')

# ---------------------------------------------------------------- the do-nothing group
PLUGS = [('Base Color', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'),
         ('Coat Weight', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector')]
def make_pass_group():
    g = bpy.data.node_groups.new('KIT test / do-nothing hook', 'ShaderNodeTree')
    for n, t in PLUGS: g.interface.new_socket(n, in_out='INPUT', socket_type=t)
    for n, t in PLUGS: g.interface.new_socket(n, in_out='OUTPUT', socket_type=t)
    gi = g.nodes.new('NodeGroupInput'); go = g.nodes.new('NodeGroupOutput')
    for n, t in PLUGS: g.links.new(gi.outputs[n], go.inputs[n])
    if 'control' in args:
        mx = g.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
        mx.inputs[7].default_value = (0.98, 0.98, 0.98, 1.0)
        g.links.new(gi.outputs['Base Color'], mx.inputs[6]); g.links.new(mx.outputs[2], go.inputs['Base Color'])
    return g
PASS = make_pass_group()

def value_source(tree, sock):
    """What feeds a plug: the wire's source, or a new Value / RGB / Geometry-normal box that holds the plug's plain number."""
    if sock.is_linked: return sock.links[0].from_socket
    if sock.name == 'Normal':
        return tree.nodes.new('ShaderNodeNewGeometry').outputs['Normal']
    if sock.type == 'RGBA':
        n = tree.nodes.new('ShaderNodeRGB'); n.outputs[0].default_value = sock.default_value; return n.outputs[0]
    n = tree.nodes.new('ShaderNodeValue'); n.outputs[0].default_value = sock.default_value; return n.outputs[0]

def splice(tree, P):
    grp = tree.nodes.new('ShaderNodeGroup'); grp.node_tree = PASS; grp.name = 'KIT hook'
    for n, _ in PLUGS:
        tree.links.new(value_source(tree, P.inputs[n]), grp.inputs[n])
    for n, _ in PLUGS:
        tree.links.new(grp.outputs[n], P.inputs[n])
    return grp

def reachable_principled(tree):
    outs = [n for n in tree.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' and n.is_active_output]
    found, groups, other = [], [], []
    seen = set()
    def walk(sock):
        for lk in sock.links:
            n = lk.from_node
            if n.name in seen: continue
            seen.add(n.name)
            if n.bl_idname == 'ShaderNodeBsdfPrincipled': found.append(n)
            elif n.bl_idname == 'ShaderNodeGroup': groups.append(n)
            elif n.bl_idname in ('ShaderNodeMixShader', 'ShaderNodeAddShader'):
                for i in n.inputs:
                    if i.type == 'SHADER': walk(i)
            else: other.append(n.bl_idname)
    for o in outs: walk(o.inputs['Surface'])
    return found, groups, other

def adapt_group(tree, gnode):
    """The add-on's shader group has no Principled box on the surface. Rebuild one box from the group's own channels (Albedo, Roughness, Normal) and
    copy the other plain numbers from the Principled box inside the group, then make that new box feed whatever the group's Shader output fed."""
    inner = [n for n in gnode.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    if not inner or not all(k in gnode.outputs for k in ('Albedo', 'Roughness', 'Normal')): return None
    src = inner[0]
    P = tree.nodes.new('ShaderNodeBsdfPrincipled'); P.name = 'KIT adapter Principled'
    for i in src.inputs:
        if i.name in P.inputs and not i.is_linked and i.name not in ('Base Color', 'Roughness', 'Normal') and hasattr(i, 'default_value'):
            try: P.inputs[i.name].default_value = i.default_value
            except Exception: pass
    tree.links.new(gnode.outputs['Albedo'], P.inputs['Base Color']); tree.links.new(gnode.outputs['Roughness'], P.inputs['Roughness'])
    tree.links.new(gnode.outputs['Normal'], P.inputs['Normal'])
    for lk in list(gnode.outputs['Shader'].links): tree.links.new(P.outputs['BSDF'], lk.to_socket)
    return P

stats = defaultdict(list)
def apply_hook(do_it=True):
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree is None or m.users == 0: continue
        t = m.node_tree
        fam = mat_fam.get(m.name, 'other')
        P, G, other = reachable_principled(t)
        if fam == 'glow and backdrop' or any(n.bl_idname == 'ShaderNodeEmission' for n in t.nodes) and not P and not G:
            stats['skipped: glow only'].append(m.name); continue
        if fam == 'leaves and needles':
            stats['skipped: leaves (see-through, vertex colour) - left alone on purpose'].append(m.name); continue
        if P:
            kind = 'plain Principled'
            for p in P: splice(t, p) if do_it else None
            stats[kind].append(m.name)
        elif G:
            done = False
            for g in G:
                newP = adapt_group(t, g)
                if newP is not None:
                    splice(t, newP); done = True
            stats['add-on shader group (adapter)' if done else 'FAILED: group without Principled'].append(m.name)
        else:
            stats['FAILED: nothing to hook'].append(m.name + ' ' + str(other))

# ---------------------------------------------------------------- render settings: small, deterministic
r = scene.render; r.resolution_x = WIDTH; r.resolution_y = int(WIDTH * 2 / 3); r.resolution_percentage = 100
scene.cycles.samples = SAMPLES; scene.cycles.use_adaptive_sampling = False; scene.cycles.use_denoising = False; scene.cycles.seed = 7
scene.cycles.device = 'CPU'; r.image_settings.file_format = 'OPEN_EXR'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '32'   # full floating-point numbers, so even a tiny difference shows
def draw(path):
    r.filepath = path; bpy.ops.render.render(write_still=True)
def load(path):
    img = bpy.data.images.load(path, check_existing=False); img.colorspace_settings.name = 'Non-Color'; a = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(img); return a

say('drawing BEFORE')
draw(PREFIX + '_before.exr'); say('before done')
apply_hook(True)
say('hook applied: ' + json.dumps({k: len(v) for k, v in stats.items()}))
draw(PREFIX + '_after.exr'); say('after done')
a, b = load(PREFIX + '_before.exr'), load(PREFIX + '_after.exr')
d = np.abs(a - b)
res = {'width': WIDTH, 'samples': SAMPLES, 'dots': int(len(a)), 'largest_difference_0_to_1': float(d.max()), 'dots_that_differ_by_more_than_one_8bit_step': int((d.max(1) > 1 / 255).sum()),
       'dots_that_differ_at_all': int((d.max(1) > 0).sum()), 'mean_difference': float(d.mean()),
       'materials': {k: len(v) for k, v in stats.items()}, 'material_lists': {k: sorted(v)[:60] for k, v in stats.items()}}
json.dump(res, open(PREFIX + '_result.json', 'w'), indent=1)
say('compare: ' + json.dumps({k: v for k, v in res.items() if k not in ('material_lists',)}))
