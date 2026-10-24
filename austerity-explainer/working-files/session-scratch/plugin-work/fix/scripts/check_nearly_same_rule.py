# What this does: re-checks the "nearly the same" rule on pictures already drawn, without drawing anything.
# It reads the per-camera numbers (mean difference, changed share) saved in each variations-result.json
# and calls each pair "nearly the same" under the OLD rule (mean AND share under their limits in every camera)
# and the NEW rule (share under its limit in every camera; the mean alone no longer makes a pair different).
# Then it compares the free scouts with the real card batches they were drawn to match.
import json, sys

BATCHING = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/batching'
CARD = {'mean': 0.6, 'share': 0.004}
SCOUT = {'mean': 0.75, 'share': 0.003}


def load_pairs(path):
    data = json.load(open(path))
    return {tuple(sorted((p['a'], p['b']))): p['per_camera'] for p in data['pairs']}


def same_old(per_camera, limits):
    return all(v['mean_difference'] < limits['mean'] and v['changed_share'] < limits['share'] for v in per_camera.values())


def same_new(per_camera, limits):
    return all(v['changed_share'] < limits['share'] for v in per_camera.values())


def called(pairs, rule, limits):
    return {key for key, per_camera in pairs.items() if rule(per_camera, limits)}


for name, card_path, scout_path in [
        ('moss', BATCHING + '/proof/moss-variations-run/variations-result.json', BATCHING + '/opus/validate/moss-scout/variations-result.json'),
        ('cracks', BATCHING + '/proof/cracks-variations-run/variations-result.json', BATCHING + '/opus/validate/cracks-scout/variations-result.json')]:
    card, scout = load_pairs(card_path), load_pairs(scout_path)
    common = set(card) & set(scout)
    print(f'== {name}: {len(card)} card pairs, {len(scout)} scout pairs, {len(common)} in both')
    for label, rule in (('OLD', same_old), ('NEW', same_new)):
        card_same = called({k: card[k] for k in common}, rule, CARD)
        scout_same = called({k: scout[k] for k in common}, rule, SCOUT)
        print(f'  {label}: card calls {len(card_same)} nearly the same, scout calls {len(scout_same)}; agree on {len(card_same & scout_same)};'
              f' scout extra {sorted(scout_same - card_same)}; scout missed {sorted(card_same - scout_same)}')
    # the closest pairs that are called different under the new rule (margin)
    rows = []
    for key in common:
        c, s = card[key], scout[key]
        rows.append((max(v['changed_share'] for v in c.values()), max(v['changed_share'] for v in s.values()),
                     max(v['mean_difference'] for v in c.values()), key))
    rows.sort()
    print('  closest by changed share (card share max, scout share max, card mean max, pair):')
    for row in rows[:max(4, 1)] + [r for r in rows if r[0] >= CARD['share']][:4]:
        print(f'    card {row[0]*100:.3f}%  scout {row[1]*100:.3f}%  card mean {row[2]:.2f}  {row[3]}')

if len(sys.argv) > 1:
    for path in sys.argv[1:]:
        pairs = load_pairs(path)
        limits = SCOUT if 'scout' in path else CARD
        print('==', path)
        for key, per_camera in sorted(pairs.items()):
            print(f'  {key}: old {"SAME" if same_old(per_camera, limits) else "diff"}, new {"SAME" if same_new(per_camera, limits) else "diff"};',
                  ', '.join(f'{cam}: mean {v["mean_difference"]:.2f} share {v["changed_share"]*100:.3f}%' for cam, v in per_camera.items()))
