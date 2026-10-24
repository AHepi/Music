# Writes the first rough "mossy Japanese courtyard" look as a file of dial values (presets/mossy_courtyard_rough.json). A look is dial values only: no code.
import json, sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
base = json.load(open(KIT + '/presets/mossy_courtyard_kept.json'))
look = json.loads(json.dumps(base))
look['id'] = 'mossy_courtyard_rough'
look['note'] = ("FIRST ROUGH PASS for the reuse proof (21 October): a kept Japanese temple courtyard that has been left to weather for some years: moss on the stones, the lantern and the roof edges, "
                "lichen on the rough stone, water and rot stains at the post feet and under the roof drips, pale streaks on the plaster under the wall caps, weeds in the gravel edge and "
                "between the stepping stones, cracks and chips in the stone. No coal soot, no coal-town rubbish, no iron. Dial values only; every number is a first guess to be tuned in the next job.")
L = look['layers']
def put(layer, **kw):
    for k, v in kw.items():
        L[layer][k] = v            # a dial the kept look does not list is a builder's finer dial: apply() checks every name against the full table
ROUND = int(sys.argv[1]) if len(sys.argv) > 1 else 1
put('soot', amount=0.9, grey_pull=0.0, film_mult=0.97, sheltered_mult=0.85, mottle_contrast=0.7, mottle_stretch=4.0, mottle_size=1.5, washed_share=0.25)
put('runoff', strength=1.0, edge_dark=0.3, width_dots=12.0, length_mult=1.5, source_share=1.0, eave_streaks=1.0, inflate_limit=8.0)
put('foot', splash_strength=0.5, splash_height=0.35, tide_share=0.6, tide_strength=0.5, tide_green=0.7, salt_bloom=0.02, mortar_wear=0.0)
put('wallgrowth', moss_amount=0.6, algae_amount=1.0, lichen_amount=0.2, saturation=0.7, hue=105.0, drip_moss=0.8, cap_moss=1.0, roof_moss=0.8, moss_value=0.22, brightness_floor=0.15)
put('wallcracks', crack_amount=0.8, crack_dots=4.5, crack_contrast=0.16, corner_chips=0.5, plaster_cracks=0.3, spall_patches=0.4, near_only=20.0)
put('dirt', film=0.5, water_marks=0.8)
put('groundmoss', patch_moss=0.35, algae_fan=0.5, liverwort=0.3, moss_value=0.25)
put('growth', weeds_amount=1.2, cushions_amount=0.7, weed_cover=0.008, wall_foot_share=0.08, cushion_cover=0.02, max_pieces=4000.0)
json.dump(look, open(KIT + '/presets/mossy_courtyard_rough.json', 'w'), indent=1)
print('look written')
