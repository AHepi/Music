# What this does (plain words): measures how much time the DAMAGE layer adds to a bake. Inside one Blender run it builds the recipe twice, once
# WITHOUT the damage layer (recipe.stack_order leaves it out) and once WITH it, and times the colour picture of each (twice each, alternating,
# because the first picture of a run includes compiling the shader). It also counts the nodes in the DAMAGE box. The computer is shared with other
# helpers, so the wall-clock seconds are noisy; 'cpu_seconds_all_threads' is the computer time the render really used (it does not grow when other programs
# are running), and cpu_seconds / 2 is about what a bake with two threads would take on an otherwise idle computer. The difference between the two variants is what matters.
# Use (inside Blender):  blender -b --disable-autoexec -t 2 --python time_it_damage.py -- SIZE OUT_JSON
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402
import bpy  # noqa: E402


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    size, out = int(arguments[0]), arguments[1]
    recipe = bh.load_recipe(os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'))
    scene, tile = bh.new_bake_scene(size)
    variants = [('without damage', {'recipe.stack_order': 'colour_and_fade,moss,outline_and_shadow'}), ('with damage', {})]
    results = []
    tmp = os.path.join(HERE, 'timing_tmp.png')
    for round_index in range(1):
        for label, params in variants:
            group = recipe.build_node_group(dict(params))
            for channel in ('Colour', 'Height'):
                material = bh.show_channel_material(group, channel)
                tile.data.materials.clear()
                tile.data.materials.append(material)
                started, cpu_started = time.time(), time.process_time()
                bh.render_to(scene, tmp, channel != 'Colour', channel == 'Height')
                results.append({'round': round_index, 'variant': label, 'channel': channel, 'seconds': round(time.time() - started, 1),
                                'cpu_seconds_all_threads': round(time.process_time() - cpu_started, 1)})
                print(results[-1], flush=True)
    damage_groups = [g for g in bpy.data.node_groups if g.name.startswith('DAMAGE')]
    info = {'size': size, 'timings': results, 'damage_group_nodes': len(damage_groups[-1].nodes) if damage_groups else None,
            'all_groups_nodes': {g.name: len(g.nodes) for g in bpy.data.node_groups if g.name in ('DAMAGE', 'LAYOUT', 'COMBINE', 'COLOUR AND FADE', 'MOSS', 'OUTLINE AND SHADOW')}}
    json.dump(info, open(out, 'w'), indent=1)
    if os.path.exists(tmp):
        os.remove(tmp)


if __name__ == '__main__':
    main()
