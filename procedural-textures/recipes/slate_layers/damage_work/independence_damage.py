# What this does (plain words): proves that the DAMAGE layer is independent of the other layers, in both directions.
#  (a) Change DAMAGE only (its Amount to 0, or its Seed + 1): the finished colour, height and roughness may change ONLY where damage is,
#      that is inside the damage Mask of the normal picture OR of the changed picture (a new seed puts damage in new places, so both count).
#      Anything else that changes is a leak and is counted. (The existing tests/independence_test.py only looks at the normal picture's
#      Mask, which is too strict for a seed change; this test uses both.)
#  (b) Change ANOTHER layer only (the Seed of COLOUR AND FADE, MOSS or OUTLINE AND SHADOW): DAMAGE's own Mask, Colour, Height and Roughness
#      (read through debug views) must come out exactly the same, because DAMAGE reads nothing but the layout bundle and its own settings.
#  (c) Change the LAYOUT seed: the slates change, so damage changes with them (it reads the bundle): that row is expected to change.
# The finished-picture comparison uses 4 samples per dot with the same sample positions in every run, so unchanged dots are bit-equal.
# Use (plain python):  python3 -I independence_damage.py [SIZE] [OUT_FOLDER]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 384
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', 'tests', 'damage_independence')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
BAKE_TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
DEFAULT_SEEDS = {'layout': 1.0, 'colour_and_fade': 11.0, 'damage': 21.0, 'moss': 31.0, 'outline_and_shadow': 41.0}
LIMITS = {'colour': 2 / 255, 'height': 0.002, 'roughness': 0.005}


def run(name, params):
    """Bake the finished picture (colour, height, roughness) and DAMAGE's own four views for one variant."""
    folder = os.path.join(OUT, name)
    views = {'view': {}}
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(views), json.dumps(params), 'Colour,Height,Roughness'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    own = {f'own_{kind}': {'debug_view': f'damage.{kind}'} for kind in ('mask', 'colour', 'height', 'roughness')}
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(own), json.dumps(params), 'Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, name, suffix):
    image = cv2.imread(os.path.join(folder, name + suffix), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def damage_mask(folder):
    return load(folder, 'own_mask', '_height.png').max(axis=2) > 0.01


def finished_changes(base, variant):
    out = {}
    for kind, suffix in (('colour', '_colour.png'), ('height', '_height.png'), ('roughness', '_roughness.png')):
        a, b = load(base, 'view', suffix), load(variant, 'view', suffix)
        out[kind] = np.abs(a - b).max(axis=2) > LIMITS[kind]
    return out


def own_views_changed(base, variant):
    """Share of dots where DAMAGE's own mask / colour / height / roughness view differs between the two bakes."""
    shares = {}
    for kind, limit in (('mask', 0.002), ('colour', 0.002), ('height', 0.002), ('roughness', 0.002)):
        a, b = load(base, f'own_{kind}', '_height.png'), load(variant, f'own_{kind}', '_height.png')
        shares[kind] = float(100 * (np.abs(a - b).max(axis=2) > limit).mean())
    return shares


def main():
    os.makedirs(OUT, exist_ok=True)
    base = run('base', {})
    base_mask = damage_mask(base)
    rows = []
    # (a) change DAMAGE only
    for label, params in (('damage Amount 0', {'damage.amount': 0.0}), ('damage Seed + 1', {'damage.seed': DEFAULT_SEEDS['damage'] + 1})):
        folder = run(label.replace(' ', '_').replace('+', 'plus'), params)
        allowed = base_mask | damage_mask(folder)
        changes = finished_changes(base, folder)
        row = {'changed': label, 'what is checked': 'finished picture: dots changed, and dots changed OUTSIDE damage masks (normal and changed)'}
        for kind, changed in changes.items():
            row[f'{kind} changed %'] = round(float(100 * changed.mean()), 3)
            row[f'{kind} changed outside damage masks %'] = round(float(100 * (changed & ~allowed).mean()), 3)
        row['damage mask share of dots % (normal / changed)'] = f'{100 * base_mask.mean():.2f} / {100 * damage_mask(folder).mean():.2f}'
        rows.append(row)
    # (b) change ANOTHER layer: damage's own views must be identical
    for layer in ('colour_and_fade', 'moss', 'outline_and_shadow'):
        label = f'{layer} Seed + 1'
        folder = run(label.replace(' ', '_').replace('+', 'plus'), {f'{layer}.seed': DEFAULT_SEEDS[layer] + 1})
        row = {'changed': label, 'what is checked': "DAMAGE's own Mask, Colour, Height, Roughness (share of dots that differ, %)"}
        row.update({f'damage {k} differs %': round(v, 4) for k, v in own_views_changed(base, folder).items()})
        rows.append(row)
    # (c) change the LAYOUT seed: damage must follow the new slates
    folder = run('layout_Seed_plus_1', {'layout.seed': DEFAULT_SEEDS['layout'] + 1})
    row = {'changed': 'layout Seed + 1', 'what is checked': "DAMAGE's own views (expected to change: it reads the layout bundle)"}
    row.update({f'damage {k} differs %': round(v, 4) for k, v in own_views_changed(base, folder).items()})
    rows.append(row)
    json.dump(rows, open(os.path.join(OUT, 'damage_independence_results.json'), 'w'), indent=1)
    lines = []
    lines.append('| changed | colour changed % | colour outside damage masks % | height changed % | height outside damage masks % | roughness changed % | roughness outside damage masks % | damage mask share of dots % (normal / changed) |')
    lines.append('|---|---|---|---|---|---|---|---|')
    for r in rows[:2]:
        lines.append(f"| {r['changed']} | {r['colour changed %']} | {r['colour changed outside damage masks %']} | {r['height changed %']} | {r['height changed outside damage masks %']} | "
                     f"{r['roughness changed %']} | {r['roughness changed outside damage masks %']} | {r['damage mask share of dots % (normal / changed)']} |")
    lines.append('')
    lines.append("| changed | damage Mask differs % | damage Colour differs % | damage Height differs % | damage Roughness differs % |")
    lines.append('|---|---|---|---|---|')
    for r in rows[2:]:
        lines.append(f"| {r['changed']} | {r['damage mask differs %']} | {r['damage colour differs %']} | {r['damage height differs %']} | {r['damage roughness differs %']} |")
    text = '\n'.join(lines) + '\n'
    open(os.path.join(OUT, 'damage_independence_table.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main()
