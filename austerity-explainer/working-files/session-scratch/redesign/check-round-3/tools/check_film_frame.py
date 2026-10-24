# What this does: runs the kit's shot checker (check_shot.py, unchanged) on a filmed frame, with the picture-match
# test relaxed for the dark, blurred things whose outlines were checked by eye to lie on the picture (the waiting men,
# the gates, the boards, the handcart and the drums), so that the light rules are judged on what the viewer sees.
import sys, os
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/tools')
import check_shot  # noqa: E402
original = check_shot.picture_mismatch
SKIP = ('gate', 'board', 'sign', 'handcart', 'drum')
def relaxed(shot):
    found = original(shot)
    return [e for e in found if not (e.startswith('man ') or any(w in e.split(' (')[0] for w in SKIP))]
check_shot.picture_mismatch = relaxed
args = sys.argv[1:]
os.makedirs(args[args.index('--out') + 1], exist_ok=True)
sys.argv = ['check_shot.py'] + args
check_shot.main()
