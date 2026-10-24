import bpy, sys, runpy
g = bpy.data.node_groups['PK Dirt']
for n in g.nodes:
    if n.bl_idname == 'ShaderNodeMix' and n.data_type == 'RGBA':
        b = n.inputs['B']
        if not b.links:
            b.default_value = (1.0, 0.0, 0.0, 1.0)
            print('SET RED on', n.name)
sys.argv = [sys.argv[0], '--', 'probe2/dbg_red.jpg', '800', '520', '8', '4.5', '-5.5', '2.4', '-0.3', '0', '1.1']
runpy.run_path('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/kit/preview.py', run_name='__main__')
