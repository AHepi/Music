import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond')
import bpy, stage_pond
for i in range(2):
    stage_pond.apply({"steps":["maple","pine"]})
    for mn in ('Bark','GARDEN bark.pine'):
        nt=bpy.data.materials[mn].node_tree
        b=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
        print("RUN",i,mn,"nodes",len(nt.nodes),"links",len(nt.links),"base colour linked",b.inputs['Base Color'].is_linked, "from", b.inputs['Base Color'].links[0].from_node.name if b.inputs['Base Color'].is_linked else None, "G6 nodes", [n.name for n in nt.nodes if n.name.startswith('G6')])
