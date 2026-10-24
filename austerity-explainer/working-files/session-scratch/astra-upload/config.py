"""Versioned, data-only settings. Loading a preset never edits scene assets."""
from copy import deepcopy
import json
import math
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
ADDON_VERSION = "0.2.0"
FAMILIES = ("wood", "plaster", "stone", "slate", "painted_metal", "fabric")
DEFAULT = {
    "schema_version": SCHEMA_VERSION,
    "preset_id": "neutral_identity",
    "art_status": "neutral_identity",
    "material": {
        "enabled": False, "family": "wood", "slot_scope": "ACTIVE",
        "blend": 0.0, "size": 0.64, "smooth": 0.2, "tilt": 0.0,
        "gloss": 0.0, "scale": [4.0, 4.0, 1.0],
    },
    "geometry": {"enabled": False, "bevel_width_m": 0.0, "segments": 1,
                 "angle_degrees": 45.0},
    "lighting": {"enabled": False, "exposure_delta": 0.0, "tint": [1.0, 1.0, 1.0]},
}


def _object(value, keys, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    missing, extra = set(keys) - set(value), set(value) - set(keys)
    if missing or extra:
        raise ValueError(f"{path}: missing {sorted(missing)}, unknown {sorted(extra)}")


def _number(value, low, high, path):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{path} must be a number")
    # Compare first: converting an arbitrarily large JSON integer to float can
    # itself raise OverflowError. Out-of-range values never need that conversion.
    if not low <= value <= high or not math.isfinite(value):
        raise ValueError(f"{path} must be finite, between {low} and {high}")


def _bool(value, path):
    if not isinstance(value, bool):
        raise ValueError(f"{path} must be true or false")


def _vector(value, low, high, path):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{path} must have exactly three components")
    for i, v in enumerate(value):
        _number(v, low, high, f"{path}[{i}]")


def validate(config):
    """Reject unknown/unsupported fields rather than silently execute a partial recipe."""
    _object(config, DEFAULT, "config")
    if config["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported config version; explicit migration is required")
    if not isinstance(config["preset_id"], str) or not 1 <= len(config["preset_id"]) <= 80:
        raise ValueError("preset_id must be a nonempty string of at most 80 characters")
    if config["art_status"] not in ("neutral_identity", "experimental", "user_authored"):
        raise ValueError("Art acceptance cannot be asserted by a settings import")
    for name in ("material", "geometry", "lighting"):
        _object(config[name], DEFAULT[name], name)
        _bool(config[name]["enabled"], f"{name}.enabled")
    m, g, light = config["material"], config["geometry"], config["lighting"]
    if m["family"] not in FAMILIES:
        raise ValueError("Unknown material family; water/glass/skin/hair/foliage are excluded")
    if m["slot_scope"] not in ("ACTIVE", "ALL"):
        raise ValueError("slot_scope must be ACTIVE or ALL")
    for key, lo, hi in (("blend", 0, 1), ("size", .05, .95), ("smooth", .01, 1),
                        ("tilt", 0, .08), ("gloss", 0, .12)):
        _number(m[key], lo, hi, f"material.{key}")
    _vector(m["scale"], .01, 100.0, "material.scale")
    _number(g["bevel_width_m"], 0, .1, "geometry.bevel_width_m")
    _number(g["angle_degrees"], 1, 179, "geometry.angle_degrees")
    _number(g["segments"], 1, 4, "geometry.segments")
    if g["segments"] != int(g["segments"]):
        raise ValueError("geometry.segments must be an integer between 1 and 4")
    _number(light["exposure_delta"], -3, 3, "lighting.exposure_delta")
    _vector(light["tint"], 0, 1, "lighting.tint")
    normalized = deepcopy(config)
    normalized["geometry"]["segments"] = int(g["segments"])
    return normalized


def canonical(config):
    return json.dumps(validate(config), sort_keys=True, indent=2, allow_nan=False)


def parse(text):
    if len(text.encode("utf-8")) > 65536:
        raise ValueError("Config exceeds the 64 KiB limit")
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("Duplicate JSON key: " + key)
            value[key] = item
        return value
    def constant(value):
        raise ValueError("Nonfinite JSON number: " + value)
    try:
        return validate(json.loads(text, object_pairs_hook=pairs, parse_constant=constant))
    except (RecursionError, OverflowError) as exc:
        raise ValueError("Config has excessive nesting or an unsupported numeric magnitude") from exc


def is_effective(config, module):
    c = config[module]
    if not c["enabled"]:
        return False
    if module == "material":
        return c["blend"] > 0
    if module == "geometry":
        return c["bevel_width_m"] > 0
    return abs(c["exposure_delta"]) > 1e-12 or any(abs(v - 1) > 1e-12 for v in c["tint"])


def presets():
    return json.loads((Path(__file__).parent / "data" / "presets.json").read_text())


def load_preset(preset_id):
    for preset in presets()["presets"]:
        if preset["id"] == preset_id:
            return validate(preset["config"])
    raise ValueError("Unknown preset ID")


def _rna_float(value, low, high):
    """Normalize only float32 RNA endpoint roundoff; imported JSON stays strict."""
    epsilon = max(abs(low), abs(high), .01) * 2e-7
    if math.isfinite(value) and low - epsilon <= value <= high + epsilon:
        return min(high, max(low, value))
    return value


def from_settings(s):
    c = deepcopy(DEFAULT)
    c.update(preset_id=s.preset_id, art_status=s.art_status)
    c["material"].update(enabled=s.material_enabled, family=s.family,
        slot_scope=s.slot_scope, blend=s.blend, size=s.size, smooth=s.smooth,
        tilt=s.tilt, gloss=s.gloss, scale=list(s.mark_scale))
    c["geometry"].update(enabled=s.geometry_enabled, bevel_width_m=s.bevel_width_m,
        segments=s.bevel_segments, angle_degrees=s.bevel_angle)
    c["lighting"].update(enabled=s.lighting_enabled, exposure_delta=s.light_ev,
                         tint=list(s.light_tint))
    for key, low, high in (("blend", 0, 1), ("size", .05, .95), ("smooth", .01, 1),
                           ("tilt", 0, .08), ("gloss", 0, .12)):
        c["material"][key] = _rna_float(c["material"][key], low, high)
    c["material"]["scale"] = [_rna_float(v, .01, 100) for v in c["material"]["scale"]]
    c["geometry"]["bevel_width_m"] = _rna_float(c["geometry"]["bevel_width_m"], 0, .1)
    c["geometry"]["angle_degrees"] = _rna_float(c["geometry"]["angle_degrees"], 1, 179)
    c["lighting"]["exposure_delta"] = _rna_float(c["lighting"]["exposure_delta"], -3, 3)
    c["lighting"]["tint"] = [_rna_float(v, 0, 1) for v in c["lighting"]["tint"]]
    # A manually edited neutral preset cannot claim neutrality in an exported config.
    if c["art_status"] == "neutral_identity" and any(is_effective(c, key) for key in ("material", "geometry", "lighting")):
        c["art_status"] = "user_authored"
        c["preset_id"] = "user_authored_from_neutral"
    return validate(c)


def to_settings(config, s):
    c = validate(config)
    s.preset_id, s.art_status = c["preset_id"], c["art_status"]
    m, g, light = c["material"], c["geometry"], c["lighting"]
    for attr, key in (("material_enabled", "enabled"), ("family", "family"),
                      ("slot_scope", "slot_scope"), ("blend", "blend"),
                      ("size", "size"), ("smooth", "smooth"), ("tilt", "tilt"),
                      ("gloss", "gloss"), ("mark_scale", "scale")):
        setattr(s, attr, m[key])
    for attr, key in (("geometry_enabled", "enabled"), ("bevel_width_m", "bevel_width_m"),
                      ("bevel_segments", "segments"), ("bevel_angle", "angle_degrees")):
        setattr(s, attr, g[key])
    s.lighting_enabled, s.light_ev, s.light_tint = light["enabled"], light["exposure_delta"], light["tint"]
    s.experimental_ack = False
