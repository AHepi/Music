"""Artist-facing explicit, undoable runtime operators. No property update handlers."""
import json
import bpy
from bpy.props import BoolProperty,EnumProperty,FloatProperty,FloatVectorProperty,IntProperty,PointerProperty,StringProperty
from . import spec,landscape,materials,native_scatter
from .vendor.courtyard_tools import api as components


def report_text(context,title,payload):
    text=bpy.data.texts.new('Astra runtime / '+title);text.write(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False))
    context.scene.astra_scene.last_report=text.name
    return text


def select(context,obj):
    for item in context.selected_objects:item.select_set(False)
    obj.hide_set(False);obj.select_set(True);context.view_layer.objects.active=obj


def to_settings(s,value):
    s.seed=value['seed'];s.detail_scale=value['detail_scale'];s.relief_height=value['relief']['height']
    s.pebble_density=value['pebbles']['density'];s.pebble_radius=value['pebbles']['radius']
    s.moss_density=value['moss']['density'];s.moss_radius=value['moss']['radius'];s.moss_body_height=value['moss']['body_height']
    s.contact_influence=value['moss']['contact_influence'];s.shelter_influence=value['moss']['shelter_influence']
    s.has_water=value['water']['level'] is not None;s.water_level=value['water']['level'] or 0;s.shore_reach=value['water']['shore_reach']
    s.override_path_width=False
    if value['paths']:s.path_width=value['paths'][0]['width']


def from_settings(s):
    text=bpy.data.texts.get(s.config_text)
    if not text:raise ValueError('Create or load a landscape JSON Text first; explicit masks are required')
    v=spec.parse(text.as_string())
    v['seed']=s.seed;v['detail_scale']=s.detail_scale;v['relief']['height']=s.relief_height
    v['pebbles'].update(density=s.pebble_density,radius=s.pebble_radius)
    v['moss'].update(density=s.moss_density,radius=s.moss_radius,body_height=s.moss_body_height,contact_influence=s.contact_influence,shelter_influence=s.shelter_influence)
    v['water'].update(level=s.water_level if s.has_water else None,shore_reach=s.shore_reach)
    if s.override_path_width:
        for p in v['paths']:p['width']=s.path_width
    return spec.validate(v)


class ASTRA_SCENE_Settings(bpy.types.PropertyGroup):
    source:PointerProperty(name='Receiving surface',type=bpy.types.Object)
    source_bank:PointerProperty(name='Scatter source bank',type=bpy.types.Collection)
    native_text:StringProperty(name='Candidate JSON')
    config_text:StringProperty(name='Landscape JSON')
    last_report:StringProperty()
    seed:IntProperty(name='Stable seed',default=137,min=0,max=1048576)
    detail_scale:FloatProperty(name='Detail scale',default=1,min=.25,max=3)
    relief_height:FloatProperty(name='Bank relief height',default=.35,min=0,max=1.5)
    override_path_width:BoolProperty(name='Override all path widths',default=False)
    path_width:FloatProperty(name='All-path clear width',default=1.25,min=.05,max=20)
    has_water:BoolProperty(name='Use local waterline',default=False)
    water_level:FloatProperty(name='Waterline Z',default=0,min=-10000,max=10000)
    shore_reach:FloatProperty(name='Damp reach',default=.5,min=.05,max=10)
    pebble_density:FloatProperty(name='Pebble candidates / area',default=20,min=0,max=50)
    pebble_radius:FloatProperty(name='Pebble radius',default=.065,min=.015,max=.25)
    moss_density:FloatProperty(name='Moss candidates / area',default=13,min=0,max=50)
    moss_radius:FloatProperty(name='Moss cushion radius',default=.19,min=.03,max=.4)
    moss_body_height:FloatProperty(name='Moss body height',default=.055,min=.012,max=.15)
    contact_influence:FloatProperty(name='Contact influence',default=.65,min=0,max=1)
    shelter_influence:FloatProperty(name='Shelter influence',default=.7,min=0,max=1)
    plank_length:FloatProperty(name='Run length',default=4,min=.5,max=20)
    plank_width:FloatProperty(name='Run width',default=1.3,min=.2,max=4)
    plank_count:IntProperty(name='Boards',default=14,min=3,max=100)
    plank_variation:FloatProperty(name='Width / edge variation',default=.24,min=0,max=.4)
    plank_gap:FloatProperty(name='Clear gap',default=.018,min=.003,max=.06)
    family:EnumProperty(name='Explicit substrate',items=[('timber','Timber','Grain-aligned bounded checks'),('stone','Stone','Angular shallow fissure'),('ceramic','Ceramic','Sparse edge notch')],default='timber')
    detail_depth:FloatProperty(name='Normal detail depth',default=.004,min=0,max=.008)
    detail_strength:FloatProperty(name='Normal strength',default=.45,min=0,max=1)
    detail_stain:FloatProperty(name='Local check stain',default=.24,min=0,max=.4)
    pigment_kind:EnumProperty(name='Pigment field',items=[('timber','Timber','Generated timber pigment'),('plaster','Plaster','Generated plaster pigment')],default='timber')
    grain_axis:EnumProperty(name='Local grain axis',items=[(a,a,'Local '+a) for a in 'XYZ'],default='X')
    pigment_strength:FloatProperty(name='Pigment strength',default=.75,min=0,max=1)
    pigment_palette:FloatVectorProperty(name='Mean linear pigment',subtype='COLOR',size=3,default=(.1,.06,.03),min=0,max=1)
    textile_strength:FloatProperty(name='Textile overlay strength',default=0,min=0,max=1)
    component_width:FloatProperty(name='Roof width / stone length',default=4.2,min=.2,max=18)
    component_depth:FloatProperty(name='Roof half-depth / stone width',default=1.45,min=.2,max=6)
    component_height:FloatProperty(name='Roof rise / stone height',default=.75,min=.2,max=5)


class Op:
    bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context):return context.mode=='OBJECT'
    def execute(self,context):
        try:return self.run(context)
        except (ValueError,TypeError,RuntimeError,KeyError,FileNotFoundError) as e:
            self.report({'ERROR'},str(e));return {'CANCELLED'}


class ASTRA_SCENE_Starter(Op,bpy.types.Operator):
    bl_idname='astra_scene.starter';bl_label='Make Starter Mask JSON'
    bl_description='Create explicit starting zones for this receiver. Review paths, supports, contacts and shelter in Text before building'
    def run(self,c):
        s=c.scene.astra_scene;source=s.source or c.active_object;pre=landscape.ensure_source(source);s.source=source
        v=spec.default_spec(pre['bounds'],s.seed);t=report_text(c,'landscape input',v);s.config_text=t.name;to_settings(s,v)
        self.report({'INFO'},'Starter masks created. Review explicit paths/support zones in Text; no geometry changed');return {'FINISHED'}


class ASTRA_SCENE_Load(Op,bpy.types.Operator):
    bl_idname='astra_scene.load_json';bl_label='Load JSON Controls'
    def run(self,c):
        s=c.scene.astra_scene;t=bpy.data.texts.get(s.config_text)
        if not t:raise ValueError('Choose a JSON Text')
        to_settings(s,spec.parse(t.as_string()));return {'FINISHED'}


class ASTRA_SCENE_Export(Op,bpy.types.Operator):
    bl_idname='astra_scene.export_json';bl_label='Export Current Controls'
    def run(self,c):
        s=c.scene.astra_scene;t=report_text(c,'landscape input',from_settings(s));s.config_text=t.name;return {'FINISHED'}


class ASTRA_SCENE_Create(Op,bpy.types.Operator):
    bl_idname='astra_scene.create';bl_label='Build Reversible Landscape'
    bl_description='Generate grounded clusters and relief on a retained receiver copy; only explicit masks protect supports'
    def run(self,c):
        s=c.scene.astra_scene;root=landscape.create(s.source,from_settings(s));select(c,root)
        t=report_text(c,'landscape checks',landscape.audit(root));self.report({'INFO'},'Built. Inspect actual hero/near renders; checks: '+t.name);return {'FINISHED'}


class ASTRA_SCENE_ReadActive(Op,bpy.types.Operator):
    bl_idname='astra_scene.read_active';bl_label='Load Active Landscape'
    def run(self,c):
        root=landscape.get_root(c.active_object)
        if root['astra_kind']!='landscape':raise ValueError('Select a landscape')
        v=spec.parse(root['astra_spec']);s=c.scene.astra_scene;s.source=root['astra_source'];s.config_text=report_text(c,'landscape input',v).name;to_settings(s,v);return {'FINISHED'}


class ASTRA_SCENE_Rebuild(Op,bpy.types.Operator):
    bl_idname='astra_scene.rebuild';bl_label='Rebuild Active Landscape'
    def run(self,c):
        root=landscape.rebuild(c.active_object,from_settings(c.scene.astra_scene));select(c,root);report_text(c,'landscape checks',landscape.audit(root));return {'FINISHED'}


class ASTRA_SCENE_Restore(Op,bpy.types.Operator):
    bl_idname='astra_scene.restore';bl_label='Restore Retained Source'
    def run(self,c):
        o=c.active_object
        if o and (o.get('astra_surface_transaction') or o.get('astra_kind')=='surface'):r=materials.restore(o)
        elif o and o.get('astra_kind')=='native_scatter':
            o.hide_render=True;o.hide_set(True);o['astra_active']=False;r={'hidden':True,'sources':'Retained unchanged; generated host retained'}
        else:r=landscape.restore(o)
        report_text(c,'restore',r);self.report({'INFO'},'Source restored; generated data retained hidden');return {'FINISHED'}


class ASTRA_SCENE_Audit(Op,bpy.types.Operator):
    bl_idname='astra_scene.audit';bl_label='Check Source / Coverage / View'
    def run(self,c):
        o=c.active_object
        r=materials.audit(o) if o and (o.get('astra_surface_transaction') or o.get('astra_kind')=='surface') else (native_scatter.audit(o) if o and o.get('astra_kind')=='native_scatter' else landscape.audit(o))
        t=report_text(c,'invariants and view',r);self.report({'INFO'},'Evidence and limits in '+t.name);return {'FINISHED'}



class ASTRA_SCENE_Native(Op,bpy.types.Operator):
    bl_idname='astra_scene.native_scatter';bl_label='Build Live Candidate Scatter'
    bl_description='Validate explicit receiver-local candidate records, retain source bank IDs, then build native Geometry Nodes controls'
    def run(self,c):
        s=c.scene.astra_scene;text=bpy.data.texts.get(s.native_text)
        if not text:raise ValueError('Choose a Text with astra.scatter/1 JSON candidate records')
        v=spec.load_json(text.as_string());spec.fields(v,['schema','kind','records','controls'])
        if v['schema']!='astra.scatter/1':raise ValueError('Unsupported scatter schema')
        o=native_scatter.create_native_scatter('Astra / Live candidate scatter',v['records'],s.source_bank,s.source,c.scene.collection,v['kind'],controls=v['controls'])
        select(c,o);report_text(c,'native scatter checks',native_scatter.audit(o));return {'FINISHED'}


class ASTRA_SCENE_Planks(Op,bpy.types.Operator):
    bl_idname='astra_scene.planks';bl_label='Create Varied Planked Run'
    def run(self,c):
        s=c.scene.astra_scene;o=landscape.create_planks(s.plank_length,s.plank_width,s.plank_count,s.seed,s.plank_variation,s.plank_gap,location=tuple(c.scene.cursor.location));select(c,o);return {'FINISHED'}


class ASTRA_SCENE_Detail(Op,bpy.types.Operator):
    bl_idname='astra_scene.detail';bl_label='Apply Material-Specific Detail'
    def run(self,c):
        s=c.scene.astra_scene;materials.apply_detail(c.active_object,s.family,s.seed,s.detail_depth,s.detail_strength,s.detail_stain)
        report_text(c,'surface checks',materials.audit(c.active_object));return {'FINISHED'}


class ASTRA_SCENE_Pigment(Op,bpy.types.Operator):
    bl_idname='astra_scene.pigment';bl_label='Apply Private Pigment Field'
    def run(self,c):
        s=c.scene.astra_scene;o=c.active_object
        materials.apply_pigment(o,o.active_material_index if o else 0,s.pigment_kind,s.grain_axis,s.seed%10001,s.pigment_strength,palette_mean=s.pigment_palette);return {'FINISHED'}


class ASTRA_SCENE_Textile(Op,bpy.types.Operator):
    bl_idname='astra_scene.textile';bl_label='Set Qualified Fabric Overlay'
    def run(self,c):
        s=c.scene.astra_scene;o=c.active_object
        materials.apply_textile(o,o.active_material_index if o else 0,s.textile_strength);return {'FINISHED'}


class ASTRA_SCENE_Roof(Op,bpy.types.Operator):
    bl_idname='astra_scene.roof';bl_label='Create Complete Ceramic Roof'
    def run(self,c):
        s=c.scene.astra_scene;o=components.create_roof(spec=components.RoofSpec(width=s.component_width,half_depth=s.component_depth,rise=s.component_height,seed=s.seed),location=tuple(c.scene.cursor.location));select(c,o);return {'FINISHED'}


class ASTRA_SCENE_Stone(Op,bpy.types.Operator):
    bl_idname='astra_scene.stone';bl_label='Create Seated Chiseled Stone'
    def run(self,c):
        s=c.scene.astra_scene;o=components.create_stone(spec=components.StoneSpec(length=s.component_width,width=s.component_depth,height=s.component_height,seed=s.seed),location=tuple(c.scene.cursor.location));select(c,o);return {'FINISHED'}


class ASTRA_SCENE_Panel(bpy.types.Panel):
    bl_label='Transferable Scene Tools 0.2.0';bl_idname='ASTRA_PT_scene';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Astra Paint'
    def draw(self,c):
        l=self.layout;s=c.scene.astra_scene
        l.label(text='Generated effects; human art review pending',icon='INFO')
        l.prop(s,'source');l.operator('astra_scene.starter')
        l.prop_search(s,'config_text',bpy.data,'texts');r=l.row(align=True);r.operator('astra_scene.load_json');r.operator('astra_scene.export_json')
        l.label(text='Edit zones / support exclusions in JSON Text')
        l.prop(s,'seed');l.prop(s,'detail_scale');l.prop(s,'relief_height');l.prop(s,'override_path_width')
        if s.override_path_width:l.prop(s,'path_width')
        b=l.box();b.prop(s,'has_water')
        if s.has_water:b.prop(s,'water_level');b.prop(s,'shore_reach')
        b=l.box()
        for key in ['pebble_density','pebble_radius','moss_density','moss_radius','moss_body_height','contact_influence','shelter_influence']:b.prop(s,key)
        l.operator('astra_scene.create');r=l.row(align=True);r.operator('astra_scene.read_active');r.operator('astra_scene.rebuild')
        l.operator('astra_scene.restore');l.operator('astra_scene.audit')
        l.label(text='No automatic support or beauty certification')
        if s.last_report:l.label(text='Text: '+s.last_report)



class ASTRA_SCENE_NativePanel(bpy.types.Panel):
    bl_label='Live Native Candidate Scatter';bl_idname='ASTRA_PT_scene_native';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Astra Paint';bl_parent_id='ASTRA_PT_scene';bl_options={'DEFAULT_CLOSED'}
    def draw(self,c):
        l=self.layout;s=c.scene.astra_scene;l.prop(s,'source_bank');l.prop_search(s,'native_text',bpy.data,'texts');l.operator('astra_scene.native_scatter')
        o=c.active_object
        if o and o.get('astra_kind')=='native_scatter':
            m=o.modifiers.get(o.get('astra_modifier',''))
            if m and m.type=='NODES':
                for q in m.node_group.interface.items_tree:
                    if q.item_type=='SOCKET' and q.in_out=='INPUT' and q.name in native_scatter.CONTROLS:l.prop(m,'["'+q.identifier+'"]',text=q.name)
        l.label(text='Live centre grounding; recheck changed footprints')


class ASTRA_SCENE_Components(bpy.types.Panel):
    bl_label='Planks / Roof / Stone';bl_idname='ASTRA_PT_scene_components';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Astra Paint';bl_parent_id='ASTRA_PT_scene';bl_options={'DEFAULT_CLOSED'}
    def draw(self,c):
        l=self.layout;s=c.scene.astra_scene
        for key in ['plank_length','plank_width','plank_count','plank_variation','plank_gap']:l.prop(s,key)
        l.operator('astra_scene.planks');l.separator()
        for key in ['component_width','component_depth','component_height']:l.prop(s,key)
        l.operator('astra_scene.roof');l.operator('astra_scene.stone');l.label(text='Created at 3D cursor. Limits validated first')


class ASTRA_SCENE_Materials(bpy.types.Panel):
    bl_label='Retained Surface Lessons';bl_idname='ASTRA_PT_scene_materials';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Astra Paint';bl_parent_id='ASTRA_PT_scene';bl_options={'DEFAULT_CLOSED'}
    def draw(self,c):
        l=self.layout;s=c.scene.astra_scene
        l.label(text='Active static mesh only; restore between ops')
        for key in ['family','detail_depth','detail_strength','detail_stain']:l.prop(s,key)
        l.operator('astra_scene.detail');l.separator()
        for key in ['pigment_kind','grain_axis','pigment_strength','pigment_palette']:l.prop(s,key)
        l.operator('astra_scene.pigment');l.separator();l.prop(s,'textile_strength');l.operator('astra_scene.textile');l.label(text='Fabric requires the exact Foundry graph')


CLASSES=(ASTRA_SCENE_Settings,ASTRA_SCENE_Starter,ASTRA_SCENE_Load,ASTRA_SCENE_Export,ASTRA_SCENE_Create,ASTRA_SCENE_ReadActive,ASTRA_SCENE_Rebuild,ASTRA_SCENE_Restore,ASTRA_SCENE_Audit,ASTRA_SCENE_Native,ASTRA_SCENE_Planks,ASTRA_SCENE_Detail,ASTRA_SCENE_Pigment,ASTRA_SCENE_Textile,ASTRA_SCENE_Roof,ASTRA_SCENE_Stone,ASTRA_SCENE_Panel,ASTRA_SCENE_NativePanel,ASTRA_SCENE_Components,ASTRA_SCENE_Materials)


def register():
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Scene.astra_scene=PointerProperty(type=ASTRA_SCENE_Settings)


def unregister():
    # Generated native geometry and persistent restore pointers remain in the file.
    # Disabling the extension never deletes user-visible generated assets.
    if hasattr(bpy.types.Scene,'astra_scene'):del bpy.types.Scene.astra_scene
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)
