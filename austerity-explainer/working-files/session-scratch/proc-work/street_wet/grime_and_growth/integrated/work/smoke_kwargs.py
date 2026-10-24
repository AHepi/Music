import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
import apply_weathering as aw
w = aw.apply('japanese_courtyard','mossy_courtyard_kept', soot={'film_mult':0.41}, layers=['soot','groundmoss'])
print('KW film_mult', w.kit.active['soot']['values']['film_mult'], sorted(w.kit.active))
w.remove(); print('KW removed', aw.current() is None)
