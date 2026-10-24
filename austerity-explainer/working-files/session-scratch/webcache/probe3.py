import bpy
t=bpy.data.node_groups.new('c','CompositorNodeTree')
for k in ['CompositorNodeTranslate','CompositorNodeFilter','CompositorNodeConvolve','CompositorNodeSeparateColor','CompositorNodeCombineColor','CompositorNodeImage','CompositorNodeNormalize','CompositorNodeOutputFile','CompositorNodeNormal']:
    n=t.nodes.new(k)
    print(k,[ (s.name,s.type) for s in n.inputs],[s.name for s in n.outputs])
    print('   props',[p.identifier for p in n.bl_rna.properties if not p.identifier.startswith('bl_') and p.identifier not in ('rna_type','name','label','location','width','height','dimensions','select','show_options','show_preview','hide','mute','show_texture','inputs','outputs','internal_links','parent','type','color','use_custom_color','width_hidden','warning_propagation','location_absolute','panel_states','color_tag')])
try:
    m=t.nodes.new('ShaderNodeMath'); print('ShaderNodeMath OK in compositor')
except Exception as e: print('ShaderNodeMath fail',e)
try:
    m=t.nodes.new('ShaderNodeVectorMath'); print('ShaderNodeVectorMath OK in compositor')
except Exception as e: print('VectorMath fail',e)
try:
    m=t.nodes.new('ShaderNodeMix'); print('ShaderNodeMix OK')
except Exception as e: print('Mix fail',e)
try:
    m=t.nodes.new('CompositorNodeMath'); print('CompositorNodeMath OK')
except Exception as e: print('CompositorNodeMath fail',str(e)[:80])
