# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The DIAL REGISTRY. A dial is one named number of a layer. Every layer has the six common dials (amount, seed, inflate_limit, fade_start, fade_end, wet_follow) and its own.
# The table (name, range, default, what it does) is data in apply/dial_table.json; a builder adds finer dials with register_layer().
#   * resolve(layer, look, settings, overrides): the values a layer gets = kit default, then the look file, then the set's own overrides (settings.looks.overrides), then
#     the call's overrides. A dial name that is not in the table is an error (so a typo cannot hide).
#   * The MASTER amount: one number that multiplies every layer's `amount` (Kit.set_master). Amount 0 means exactly nothing (the selftests prove it).
#   * Per-role multipliers: a few dials a set varies by role (settings apply.<layer>.role_dials, e.g. {"wall.trim": {"film_mult": 0.8}}) are written as OBJECT custom
#     properties "wk_<layer>_<dial>" (a multiplier, default 1) and read by the layer through an Attribute node; material slots are never touched. For every layer the kit also
#     writes "wk_<layer>_amount": 1 on objects whose role the layer acts on and 0 on every other object, so a material shared by two kinds of object is only weathered where the
#     set says (isolation).
# Plain Python; the Blender side (writing the properties) is in seed.py.
import json
import os

from . import KIT_ROOT
from . import settings as settings_module

TABLE_PATH = os.path.join(KIT_ROOT, 'apply', 'dial_table.json')
COMMON_NAMES = ('amount', 'seed', 'inflate_limit', 'fade_start', 'fade_end', 'wet_follow')


class LayerDials:
    def __init__(self, layer, rows, meta=None):
        self.layer = layer
        self.rows = {r['name']: r for r in rows}
        self.meta = meta or {}

    def row(self, name):
        return self.rows.get(name)

    def names(self):
        return list(self.rows)

    def defaults(self):
        return {name: r['default'] for name, r in self.rows.items()}

    def clamp(self, name, value):
        row = self.rows[name]
        return min(max(value, row['lo']), row['hi'])


class DialTable:
    def __init__(self, data):
        self.common = data['common']
        self.layers = {}
        for key, spec in data['layers'].items():
            self.register_layer(key, spec['dials'], {k: v for k, v in spec.items() if k != 'dials'})

    def register_layer(self, layer, rows, meta=None):
        """Adds (or extends) a layer's table. rows: dicts with name, lo, hi, default, doc. The common dials are added automatically; the common names may not be redefined."""
        existing = self.layers.get(layer)
        merged = {r['name']: r for r in self.common}
        if existing:
            merged.update(existing.rows)
        for row in rows:
            if row['name'] in COMMON_NAMES and row['name'] in merged and merged[row['name']] != row:
                raise ValueError(f'{layer}: the common dial {row["name"]!r} may not be redefined')
            merged[row['name']] = dict(row)
        self.layers[layer] = LayerDials(layer, list(merged.values()), meta or (existing.meta if existing else {}))
        return self.layers[layer]


def load_table(path=TABLE_PATH):
    with open(path) as handle:
        return DialTable(json.load(handle))


TABLE = load_table()


def register_layer(layer, rows, meta=None):
    return TABLE.register_layer(layer, rows, meta)


def resolve(layer, look=None, settings=None, overrides=None, strict=True):
    """The dial values of one layer: kit defaults < look < set overrides < call overrides. Returns a dict {dial: value}. Unknown dial names raise (strict)."""
    spec = TABLE.layers.get(layer)
    if spec is None:
        if strict:
            raise KeyError(f'layer {layer!r} has no dial table')
        values = {}
    else:
        values = spec.defaults()
    sources = []
    if look:
        sources.append(look.get('layers', {}).get(layer, {}))
    if settings is not None:
        sources.append(settings.look_overrides().get(layer, {}))
    sources.append(overrides or {})
    for source in sources:
        for name, value in source.items():
            if spec is not None and spec.row(name) is None:
                if strict:
                    raise KeyError(f'{layer}: unknown dial {name!r}')
                continue
            values[name] = value
    return values


def effective_amount(values, master=1.0):
    """What the layer node's Amount input gets: the layer's amount times the master."""
    return float(values.get('amount', 1.0)) * float(master)


def role_multipliers(settings, layer):
    """{role: {dial: multiplier}} for the layer, roles expanded to real role names. Only dials that exist in the layer's table are allowed (checked by validate)."""
    spec = settings.apply.get(layer, {})
    result = {}
    for role, dials in spec.get('role_dials', {}).items():
        for real in settings.expand_roles([role]):
            result.setdefault(real, {}).update(dials)
    return result


# The dials the CURRENT set varies by role, per layer ({layer: {dial, ...}}), noted by Kit.apply just before the layers are built. A walls layer multiplies exactly these dials by the
# object's role value (WallLayer.dial); a dial the set does not vary costs no node. Plain Python.
ROLE_DIAL_NAMES = {}
MIN_ROLE_MULT = 0.002      # the smallest role multiplier written: an object value of 0 reads as "the set names none" (1), so "off" is written as a hair above 0


def note_role_dials(settings):
    """Fills ROLE_DIAL_NAMES from the set's apply.<layer>.role_dials (the union over the roles). Call it before building a layer's node group."""
    ROLE_DIAL_NAMES.clear()
    for layer in settings.apply:
        names = {dial for table in role_multipliers(settings, layer).values() for dial in table}
        if names:
            ROLE_DIAL_NAMES[layer] = names
    return ROLE_DIAL_NAMES


def object_attribute_name(layer, dial):
    return f'wk_{layer}_{dial}'


def validate_role_dials(settings):
    report = settings_module.Report('role dials')
    for layer, spec in settings.apply.items():
        table = TABLE.layers.get(layer)
        for role, dials in spec.get('role_dials', {}).items():
            for dial in dials:
                if table is not None and table.row(dial) is None:
                    report.error(f'apply.{layer}.role_dials.{role}: unknown dial {dial!r}')
    return report
