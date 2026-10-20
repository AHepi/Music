"""Plain note: our own test. Prints the settings (properties) of Ucupaint's bake and mask commands, and of a layer's channels."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from ucu_common import *
enable()
for opname in ('y_bake_channels','y_new_layer_mask','y_bake_to_layer','y_bake_entity_to_image','y_add_new_ypaint_channel','y_set_layer_channel_blend_type'):
    op = getattr(bpy.ops.wm, opname)
    rt = op.get_rna_type()
    print('==', opname, '|', rt.description)
    for p in rt.properties:
        if p.identifier == 'rna_type': continue
        extra = ''
        if getattr(p,'enum_items',None) and p.type=='ENUM':
            extra = ' enum=' + str([i.identifier for i in p.enum_items])[:260]
        print('   ', p.identifier, p.type, getattr(p,'default',None) if p.type!='ENUM' else getattr(p,'default',None), extra)
