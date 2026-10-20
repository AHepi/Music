# What this does (plain words): measures what the OUTLINE AND SHADOW layer costs. (1) how many nodes its box has; (2) the CPU time of one picture of the
# whole recipe at SIZE dots with the layer on, with the layer left out of the stack (recipe.stack_order without it: the real cost of the layer) and
# with Amount 0 (the nodes are still built and still computed, so this is NOT the cost of the layer). CPU time ("user" seconds) is used because the machine is shared and wall time swings with the load.
# Use (plain python):  python3 -I time_it.py [SIZE]      Output: prints a small table and writes time_it.json
import json
import os
import resource
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 768
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
BAKE_TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
OUTSIDE = os.path.join(HERE, 'previews', 'time_it')


def run(params, views, channels):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.time()
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, OUTSIDE, str(SIZE), '4', json.dumps(views), json.dumps(params), channels], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return round(after.ru_utime - before.ru_utime, 1), round(time.time() - start, 1)


def main():
    result = {'size': SIZE}
    for name, params in (('layer on', {}), ('layer absent (not in the stack)', {'recipe.stack_order': 'colour_and_fade,moss,damage'}), ('layer off (Amount 0, still built and computed)', {'outline_and_shadow.amount': 0.0}), ('layer on, again', {}), ('layer absent again', {'recipe.stack_order': 'colour_and_fade,moss,damage'})):
        for channel in ('Colour', 'Height'):
            cpu, wall = run(params, {'v': {}}, channel)
            result[f'{name} {channel}: cpu seconds'] = cpu
            result[f'{name} {channel}: wall seconds'] = wall
    json.dump(result, open(os.path.join(HERE, 'time_it.json'), 'w'), indent=1)
    for k, v in result.items():
        print(k, v)


if __name__ == '__main__':
    main()
