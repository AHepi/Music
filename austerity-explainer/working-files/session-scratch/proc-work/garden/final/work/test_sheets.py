# What this does: opens a saved garden file (shapes + life done, no kit needed) and runs ONLY the weathering kit's mask reader into a throwaway folder, to see
# which wall sheets it can make. Used to test the wall-sheet patch quickly (about 40 s). Run: blender -b FILE.blend -P test_sheets.py -- OUTDIR
import bpy, sys, os, json, time
sys.dont_write_bytecode = True
FINAL = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final'
sys.path.insert(0, FINAL + '/stage/kit')
out = sys.argv[sys.argv.index('--') + 1]
import apply_weathering
from masks import reader
t = time.time()
m = reader.run('japanese_courtyard', 'courtyard', out, raw_dir=out + '_raw', sheets=True, with_shade=True)
print('SHEETS_MADE', [s['name'] for s in m['frames']['sheets']], 'errors', m['stats'].get('sheet_errors'), 'seconds', round(time.time() - t, 1))
for s in m['frames']['sheets']:
    print('SHEET', s['name'], 'plane', round(s['plane'], 3), 'u', [round(x, 2) for x in s['u_range']], 'v', [round(x, 2) for x in s['v_range']], 'size', s['size'], 'front', s['front_axis'], s['front_sign'])
