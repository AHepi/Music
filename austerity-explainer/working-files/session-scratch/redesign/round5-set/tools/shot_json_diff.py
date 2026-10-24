# What this does: lists what changed in works-shot.json between two exports (scratch, round 5): keys added or removed,
# and values changed, for the keys the pages read.
# Use: python3 shot_json_diff.py OLD.json NEW.json
import json, sys
old, new = (json.load(open(p)) for p in sys.argv[1:3])
print('keys added:', sorted(set(new) - set(old)))
print('keys removed:', sorted(set(old) - set(new)))
for key in ('views', 'gates', 'brazier', 'coals_z', 'fire_light', 'lantern', 'lantern_light', 'lunch_tin', 'gate_lamps', 'drums', 'boards',
            'no-2-crates', 'handcart', 'no-1-pop-up-crates', 'no-1-gateway', 'men', 'no_2_men', 'queue_front', 'chimney_tops', 'machines'):
    if old.get(key) != new.get(key):
        if key == 'views':
            for v in new['views']:
                for spot in ('plate', 'composed'):
                    if old['views'][v].get(spot) != new['views'][v].get(spot):
                        print(f'views.{v}.{spot}: {old["views"][v].get(spot)} -> {new["views"][v].get(spot)}')
        else:
            print(f'{key}: {json.dumps(old.get(key))[:300]} -> {json.dumps(new.get(key))[:300]}')
for k in ('men_at_no_1', 'men_at_no_2'):
    print(k, [m['feet'][:2] for m in new[k]])
