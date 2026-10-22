import json, os, sys
D = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof'
def pic(name, cam, size='960x640', samples=96, **kw):
    d = {'name': name, 'camera': cam, 'size': size, 'samples': samples, 'mode': 'preview', 'quality': 88}
    d.update(kw)
    return d
def save(name, job):
    os.makedirs(D + '/jobs', exist_ok=True)
    json.dump(job, open(D + '/jobs/' + name + '.json', 'w'), indent=1)
CH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
cams = json.load(open(CH + '/final/jobs/build_A.json'))['extra_cameras']
CLOSE = ['G6 roof cam 1', 'G6 roof cam 2', 'G6 roof cam 3', 'G6 roof cam 4', 'G6 roof cam 5', 'G6 roof cam 6',
         'G6 final cam eave A', 'G6 final cam eave B', 'G6 final cam lantern A', 'G6 final cam lantern B', 'G6 final cam lantern C',
         'G6 final cam lantern D', 'G6 final cam bridge B', 'G6 final cam bridge C']
def short(c):
    return c.replace('G6 roof cam ', 'rc').replace('G6 final cam ', '').replace(' ', '')
if __name__ == '__main__':
    which = sys.argv[1]
    if which == 'capcams':
        ex = {'capA': [[-0.8, -0.6, 2.3], [0.95, 1.1, 1.7], 50], 'capB': [[2.5, -0.2, 2.2], [0.95, 1.1, 1.7], 50], 'joint': [[-0.15, 0.2, 0.75], [0.95, 1.1, 0.35], 40]}
        cams2 = dict(cams); cams2.update(ex)
        pics = [pic(n, 'G6 final cam ' + n, '1000x667', 96) for n in ex]
        save('capcams_before', {'outdir': D + '/out/capcams', 'extra_cameras': ex, 'pictures': [dict(p, name=p['name'] + '_before') for p in pics]})
        save('capcams_after', {'outdir': D + '/out/capcams', 'apply_stages': ['wood', 'roof', 'ground', 'pond', 'final'], 'extra_cameras': cams2, 'pictures': [dict(p, name=p['name'] + '_after') for p in pics]})
    if which in ('t3', 't3before'):
        ex = {'capA': [[-0.8, -0.6, 2.3], [0.95, 1.1, 1.7], 50], 'capB': [[2.5, -0.2, 2.2], [0.95, 1.1, 1.7], 50], 'joint': [[-0.15, 0.2, 0.75], [0.95, 1.1, 0.35], 40]}
        cams2 = dict(cams); cams2.update(ex)
        names = ['G6 roof cam 2', 'G6 roof cam 3', 'G6 roof cam 4', 'G6 roof cam 5', 'G6 final cam eave A', 'G6 final cam lantern B', 'G6 final cam capA', 'G6 final cam capB', 'G6 final cam joint']
        pics = [pic('hero', 'photo', '1200x800', 128), pic('veranda', 'veranda', '1200x800', 128),
                pic('hero_roof', 'photo', '2400x1600', 192, border=[0.12, 0.70, 0.72, 0.89]), pic('hero_wall', 'photo', '2400x1600', 192, border=[0.60, 0.42, 0.98, 0.70]),
                pic('hero_rocks', 'photo', '2400x1600', 192, border=[0.03, 0.28, 0.58, 0.47]), pic('ver_lantern', 'veranda', '2400x1600', 192, border=[0.12, 0.40, 0.40, 0.80])]
        pics += [pic(short(c), c, '960x640', 96) for c in names]
        if which == 't3':
            save('t3', {'outdir': D + '/out/t3', 'apply_stages': ['wood', 'roof', 'ground', 'pond', 'final'], 'extra_cameras': cams2, 'pictures': pics})
        else:
            save('t3before', {'outdir': D + '/out/t3before', 'extra_cameras': cams2, 'pictures': pics})
    if which == 'before':
        pics = [pic('hero', 'photo', '1200x800', 128), pic('veranda', 'veranda', '1200x800', 128)] + [pic(short(c), c, '960x640', 96) for c in CLOSE]
        save('before', {'outdir': D + '/out/before', 'pictures': pics})
    elif which == 'dbg1':
        code = open(D + '/tools/dbg_exec.py').read()
        pics = []
        for c in ('G6 final cam lantern B', 'G6 final cam lantern C', 'G6 final cam lantern D', 'G6 final cam bridge B', 'G6 roof cam 5'):
            for st in ('scan', 'foot', 'dirt', 'cracks', 'growth', 'moss', 'full'):
                pics.append(pic('%s_%s' % (short(c), st), c, '640x427', 48, exec=code, dbg=st))
        save('dbg1', {'outdir': D + '/out/dbg1', 'apply_stages': ['wood', 'roof', 'ground', 'pond', 'final'], 'extra_cameras': cams, 'pictures': pics})
