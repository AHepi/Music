import sys, os, json, traceback
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond')
import stage_pond
args = sys.argv[sys.argv.index('--')+1:]
opts = json.loads(args[0]) if args else {}
try:
    rep = stage_pond.apply(opts)
    print("NUMBERS", json.dumps(rep['numbers'], default=str))
    print("CREATED", len(rep['created']), rep['created'][:12])
except Exception:
    traceback.print_exc()
