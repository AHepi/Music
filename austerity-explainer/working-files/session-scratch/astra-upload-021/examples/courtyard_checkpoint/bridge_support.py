"""Courtyard curved-deck adapter: fixed profile pitch plus independently bounded style twist.
Top joint footprint span is preserved by width/cos(pitch), with thickness compensation.
This is a geometric support repair, not a code-compliance certification.
"""
import bpy, math
from mathutils import Vector

def repair_arch_pitch(host, records, nominal_thickness=.13):
    if host.data.attributes.get('lived_plank_arch_pitch'):raise ValueError('Pitch adapter already applied')
    a=host.data.attributes.new(name='lived_plank_arch_pitch',type='FLOAT_VECTOR',domain='POINT');sc=host.data.attributes['lived_plank_scale'];half=nominal_thickness/2
    changed=[]
    for i,r in enumerate(records):
        yy=r['center'][1];t=(yy/1.4+4.65)/5.05;derivative=.28*math.pi/(1.4*5.05)*math.cos(math.pi*t);pitch=math.atan(derivative)
        a.data[i].vector=(pitch,0,0);v=host.data.vertices[i];v.co.y+=half*math.sin(pitch);v.co.z+=half*(1-math.cos(pitch));scale=sc.data[i].vector;scale.y/=math.cos(pitch);sc.data[i].vector=scale
        changed.append({'index':i,'fixed_arch_pitch_rad':pitch,'world_profile_slope':derivative,'top_span_preserved_m':r['width'],'center_before':r['center'],'center_after':list(v.co),'scale_after':list(scale),'style_rotation_unchanged':r['rotation']})
    mod=next(m for m in host.modifiers if m.type=='NODES');g=mod.node_group;inst=next(n for n in g.nodes if n.bl_idname=='GeometryNodeInstanceOnPoints');prior=inst.inputs['Rotation'].links[0].from_socket;n=g.nodes.new('GeometryNodeInputNamedAttribute');n.data_type='FLOAT_VECTOR';n.inputs['Name'].default_value='lived_plank_arch_pitch';add=g.nodes.new('ShaderNodeVectorMath');add.operation='ADD';g.links.new(prior,add.inputs[0]);g.links.new(n.outputs['Attribute'],add.inputs[1]);g.links.new(add.outputs['Vector'],inst.inputs['Rotation'])
    host.data.update();host['lived_pitch_contract']='Fixed analytic arch tangent pitch; independent style Twist. Width compensates cos(pitch); thickness compensation preserves top joints. Re-audit bearings after changing source dimensions or curve.'
    bpy.context.view_layer.update();return {'algorithm':'analytic tangent of z=.32+.28sin(pi*(y/1.4+4.65)/5.05), pitch atan(dz/dy), fixed separately from style twist','nominal_thickness_m':nominal_thickness,'boards':changed,'pitch_range_rad':[min(x['fixed_arch_pitch_rad'] for x in changed),max(x['fixed_arch_pitch_rad'] for x in changed)]}
