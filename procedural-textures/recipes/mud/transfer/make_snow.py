# What this does (plain words): the TRANSFER TEST. It makes a surface nobody gave us, a SNOWY TRACK (compacted snow with tyre ruts of grey slush, a few dark rocks poking through, blue
# meltwater puddles), with the SAME generator and the SAME sampler, changing only numbers: a new palette of 16 colours, which palette entries play which part (ground, rut band, groove,
# bank, wet streak, water), three scale numbers (fewer stones, a bit fewer puddles, fewer clods that clump into bigger zones) and the height stretch (snow is bright, so the brightness range
# that becomes height moves up). No generator code is changed. It writes transfer/snow_description.json and prints the time it took.
# Use: python3 -I make_snow.py   then bake with generator/bake_one.sh transfer/snow_description.json transfer/snow 1254
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import sampler
started = time.time()
SNOW_PALETTE = [[222, 229, 238], [58, 60, 68], [150, 176, 206], [150, 158, 172], [244, 247, 252], [120, 150, 190], [28, 28, 34], [96, 100, 112],
                [96, 128, 168], [200, 210, 224], [176, 186, 202], [170, 174, 184], [78, 76, 84], [236, 240, 248], [188, 196, 210], [88, 90, 100]]
d = sampler.sample_description(301, palette=SNOW_PALETTE, tones={'ground': 0, 'band': 3, 'groove': 7, 'bank': 4, 'wet': 5, 'water_base': 8, 'water_light': 2},
                               stone_scale=0.35, puddle_scale=0.7, clod_count=9000, zone_weight=0.85, maps={'height': {'grey_low': 60.0, 'grey_high': 245.0, 'blur': 0.5, 'mode': 'from_colour'}, 'normal': {'strength': 9}})
d['name'] = 'snowy_track_transfer'
json.dump(d, open(os.path.join(HERE, 'snow_description.json'), 'w'), separators=(',', ':'))
print('description written in', round(time.time() - started, 2), 's;', len(json.dumps(d, separators=(',', ':'))), 'bytes')
