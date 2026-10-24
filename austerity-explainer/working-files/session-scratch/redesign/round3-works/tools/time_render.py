# Times small EEVEE renders of the saved Works scene, to see where the time goes.
import bpy, time, sys
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village')
import set_dressing as dressing
out = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round3-works/prev2/'
for label, w, h, samples in (('a', 270, 480, 1), ('b', 270, 480, 8), ('c', 540, 960, 1)):
    t = time.time()
    dressing.render(out + f'time-{label}.png', w, h, samples)
    print('TIME', label, w, h, samples, round(time.time() - t, 1), flush=True)
lights = [o for o in bpy.context.scene.objects if o.type == 'LIGHT' and not o.hide_render]
print('TIME lights', len(lights), sum(1 for o in lights if o.data.use_shadow))
print('TIME images', len(bpy.data.images), sum(i.size[0] * i.size[1] for i in bpy.data.images) / 1e6, 'megapixels')
