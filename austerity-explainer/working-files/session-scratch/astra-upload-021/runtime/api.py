"""Supported API: import from <extension module>.runtime.api inside Blender 5.1.x."""
from .spec import VERSION, SCHEMA, validate, parse, default_spec
from .landscape import create as create_landscape, rebuild as rebuild_landscape
from .landscape import restore as restore_landscape, audit as audit_landscape, create_planks
from .materials import apply_pigment, apply_textile, apply_detail, restore as restore_surface, audit as audit_surface
from .vendor.courtyard_tools.api import (RoofSpec, StoneSpec, create_roof, create_stone,
    update_roof, update_stone, set_pose, bind_material)
from .native_scatter import create_native_scatter, set_controls as set_scatter_controls, audit as audit_native_scatter
