# What this does (plain words): bakes one description with the Blender generator (all pictures, 1254 dots, 16 samples) and then runs both comparison
# tools on the result, saving the numbers (scores/NAME_pixel.json, scores/NAME_texture.json) and the difference sheet (scores/NAME_diff.png).
# Use:  python3 -I bake_and_score.py NAME [description file name in description/] [--size 1254] [--samples 16] [--shift 0]
import json, os, subprocess, sys, time, shutil
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE)
import preview_tools as pt
BLENDER='/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
def opt(name,default): return sys.argv[sys.argv.index(name)+1] if name in sys.argv else default
name=sys.argv[1]; desc=sys.argv[2] if len(sys.argv)>2 and not sys.argv[2].startswith('--') else name+'.json'
size=opt('--size','1254'); samples=opt('--samples','16'); shift=opt('--shift','0')
out=PROC+'/recipes/metal/outputs/'+name+(f'_{size}' if size!='1254' else '')
t0=time.time()
r=subprocess.run([BLENDER,'-b','--disable-autoexec','-t','2','--python',HERE+'/metal_generator.py','--',PROC+'/recipes/metal/description/'+desc,out,'--size',size,'--samples',samples,'--shift',shift],capture_output=True,text=True)
if 'bake]' not in r.stdout: print(r.stdout[-1500:],r.stderr[-800:]); sys.exit(1)
bake=json.load(open(out+'/bake.json')); print(name,'baked in',round(time.time()-t0,1),'s; shapes',bake['shapes'],bake['timings'])
if size=='1254' and shift=='0':
    pixel,tex=pt.compare(out,sheet=True)
    shutil.copy(out+'/pixel.json',PROC+f'/recipes/metal/scores/{name}_pixel.json'); shutil.copy(out+'/texture.json',PROC+f'/recipes/metal/scores/{name}_texture.json'); shutil.copy(out+'/diff.png',PROC+f'/recipes/metal/scores/{name}_diff.png')
    print(name,pt.summary_line(pixel,tex)); print('  texture groups',tex['groups'])
