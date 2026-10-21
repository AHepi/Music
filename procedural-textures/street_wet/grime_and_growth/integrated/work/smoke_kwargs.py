import sys
sys.path.insert(0,'proc-work/kits/weathering')
import apply_weathering as aw
w = aw.apply('japanese_courtyard','mossy_courtyard_kept', soot={'film_mult':0.41}, layers=['soot','groundmoss'])
print('KW film_mult', w.kit.active['soot']['values']['film_mult'], sorted(w.kit.active))
w.remove(); print('KW removed', aw.current() is None)
