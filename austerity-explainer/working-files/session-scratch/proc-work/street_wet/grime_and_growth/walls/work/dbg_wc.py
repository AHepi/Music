import sys, os, json
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
import bpy
from apply import kit as kit_module
from harness import cameras, render
from masks import bus as bus_module
from walls import apply_walls
args = sys.argv[sys.argv.index('--') + 1:]
out = args[2]; layer = args[3]; cam = args[4]
os.makedirs(out, exist_ok=True)
k = kit_module.Kit.load(args[0], scene_id=args[1], strict=False); bus_module.attach(k); apply_walls.register(k)
cams, _ = cameras.make_all(k.settings, args[1]); camera = cams[cam]
k.prepare()
render.draw(out + '/base.png', 135, 240, 4, camera); base = render.read(out + '/base.png')
k.apply(layers=[layer]); k.set_dials(layer, amount=0.0)
tree = k.registry[layer].tree
res = {}
def test(name):
    render.draw(out + '/t.png', 135, 240, 4, camera); a = render.read(out + '/t.png')
    c = render.compare(base, a); res[name] = (round(c['max_diff'], 5), round(c['share_over_one_step'], 4), round(c['share_changed'], 4)); print(name, res[name], flush=True)
test('as built')
gin = [n for n in tree.nodes if n.type == 'GROUP_INPUT'][0]; gout = [n for n in tree.nodes if n.type == 'GROUP_OUTPUT'][0]
inp = gout.inputs['Coat Weight']
tree.links.remove(inp.links[0])
m = tree.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'; m.inputs[1].default_value = 1.0
tree.links.new(gin.outputs['Coat Weight'], m.inputs[0]); tree.links.new(m.outputs[0], inp)
test('coat x 1.0 (a math node)')
amt = [n for n in tree.nodes if n.type == 'ATTRIBUTE']
m2 = tree.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
tree.links.remove(inp.links[0])
m2.inputs[1].default_value = 1.0
# value from an object attribute that is 1.0? use the Amount-based factor: input x (1 + 0 x Amount)
mm = tree.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = 0.0; mm.inputs[2].default_value = 1.0
tree.links.new(gin.outputs['Amount'], mm.inputs[0])
tree.links.new(gin.outputs['Coat Weight'], m2.inputs[0]); tree.links.new(mm.outputs[0], m2.inputs[1]); tree.links.new(m2.outputs[0], inp)
test('coat x (1 + 0*Amount) (runtime expression)')
