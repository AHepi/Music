"""
What this file does: checks that object names turn into the right roles.
    python3 tests/test_roles.py          (needs the bpy module only to import; no scene is built)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'materials'))
import apply_by_role as roles  # noqa: E402

CASES = {
    'left terrace 03 wall': 'wall', 'window lit': 'window lit', 'lit window 4': 'window lit', 'window dim': 'window dim',
    'window': 'window dark', 'window surround stone': 'trim', 'door surround stone': 'trim', 'door step': 'pavement',
    'door wood': 'wood', 'kerb stone left': 'trim', 'lamp post iron 2': 'iron', 'lamp glass 2': 'lamp glass',
    'lamp cap iron 2': 'iron', 'puddle water 35': 'water', 'roof slate': 'roof', 'chimney smoke': 'smoke',
    'chimney stack wall': 'wall', 'cart wheel iron': 'iron', 'cart bed wood': 'wood', 'downpipe iron': 'iron',
    'road setts': 'road', 'pavement flags right': 'pavement', 'Cube': None, 'far hills earth': 'earth',
    'beach rippled sand plaster': 'sand', 'sea water': 'sea', 'surfboard leaning wood': 'wood', 'shore boulder stone': 'rock',
}


def main():
    for name, expected in CASES.items():
        got = roles.role_from_name(name)
        assert got == expected, f'{name!r}: expected {expected!r}, got {got!r}'
    for role, choice in roles.ROLE_MATERIALS.items():
        names = choice if isinstance(choice, list) else [choice]
        inventory = open(os.path.join(os.path.dirname(roles.MATERIALS_BLEND), 'Material inventory.txt'), encoding='utf-8').read()
        for n in names:
            if n.startswith('ROLE •'):
                continue  # made in code by apply_by_role, not taken from Materials.blend
            assert n in inventory, f'{role}: {n} is not in Materials.blend'
    print('PASS test_roles')


if __name__ == '__main__':
    main()
