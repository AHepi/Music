"""What this does: works out the numbers a wear layer uses for one material: its AMOUNT (how strongly it acts) and its DIALS (film, splash, cover, width ...).
The amount is the look's amount for the layer times the role's multiplier (roles.json) times the state for wetness (dry 0, damp as the look says, wet more); the
dials are, from weakest to strongest: the dial table's defaults, the role class's own defaults (ground has no wall-foot splash), the look's dial values and the
place settings' own overrides. A dial name that is not in the table is an error, so a typo cannot hide. Plain Python (standard library), tested without Blender.
A concrete example: dial_values('dirt', 'ground', look, settings_dials) gives {'film': 0.5, 'foot_splash': 0.0, 'polish': 0.5, ...}; layer_amount('wetness',
look, 'damp', 1.0) gives the look's wetness amount.
"""
from .. import settings_file

STATE_WETNESS = {'dry': 0.0, 'damp': 1.0, 'wet': 1.6}


def socket_name(dial):
    """The group input a dial lives on: 'foot_height_metres' -> 'Foot Height Metres'."""
    return ' '.join(word.capitalize() for word in dial.split('_'))


def table_defaults(layer):
    table = settings_file.dial_table()
    rows = list(table['common']) + list(table['layers'][layer]['dials'])
    return {row['name']: row['default'] for row in rows}, {row['name']: (row['lo'], row['hi']) for row in rows}


def dial_values(layer, role_class, look_data, settings_dials=None):
    """The dial values of one layer for a role class (see the note at the top). Unknown dial names raise KeyError."""
    values, limits = table_defaults(layer)
    roles = settings_file.roles_table()
    sources = [roles['classes'].get(role_class, {}).get('dial_defaults', {}).get(layer, {}), (look_data or {}).get('layers', {}).get(layer, {}).get('dials', {}),
               (settings_dials or {}).get(layer, {})]
    for source in sources:
        for name, value in source.items():
            if name not in values:
                raise KeyError(f'the layer "{layer}" has no dial "{name}" (its dials: {", ".join(values)})')
            low, high = limits[name]
            values[name] = min(max(value, low), high)
    return values


def layer_amount(layer, look_data, state, role_multiplier=1.0):
    """The amount of a layer on an object: the look's amount x the role's multiplier; for wetness also the state (dry 0, damp 1, wet 1.6, capped at 1)."""
    amount = float(look_data['layers'][layer]['amount']) * float(role_multiplier)
    if layer == 'wetness':
        amount *= STATE_WETNESS[state]
    return min(max(amount, 0.0), 1.0)
