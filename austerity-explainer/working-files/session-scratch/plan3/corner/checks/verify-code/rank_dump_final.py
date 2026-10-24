# runs check_shot.main() and prints each ranked problem's kind, tier and how_bad (the ranking keys)
import sys
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-code/final_mod')
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
