# runs check_shot.main() and prints each ranked problem's kind, tier and how_bad (the ranking keys)
import sys
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
original = cs.Report.rank
def rank(self):
    ranked = original(self)
    for i in ranked:
        print(f"RANK {i['number']:2d} tier {cs.TIER[i['kind']]} {i['kind']:10s} how_bad {i['how_bad']:7.2f}  {i['rule']}: {i['what'][:90]}", file=sys.stderr)
    return ranked
cs.Report.rank = rank
sys.argv = ['check_shot.py'] + sys.argv[1:]
cs.main()
