#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
python3 -I - <<'PY'
import sys
sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
import rr
rr.plan('plan_r5', ['class','dirt:tar','dirt:halo','dirt:scrub','groundcracks:flag_fine','groundcracks:flag_broken','groundcracks:flag_tilt','groundcracks:flag_chip','groundcracks:kerb_chips','groundcracks:sett_disturbed','groundcracks:sett_joints','groundcracks:flag_fine_cells','groundcracks:flag_broken_cells','groundcracks:sett_joint_all','groundmoss:joint_moss','groundmoss:joint_all','groundmoss:algae','groundmoss:liverwort','iron:foot_rust','bus:vertical_foot','bus:wall_dist','bus:keepclear','bus:footfall'])
PY
python3 -I proc-work/kits/weathering/ground/measure_period_ground.py pit_village_street proc-work/street_wet/grime_and_growth/ground/runs/plan_r5/out --out proc-work/street_wet/grime_and_growth/ground/period_r5.json
python3 -I proc-work/kits/weathering/ground/feature_report.py proc-work/street_wet/grime_and_growth/ground/runs/plan_r5/out proc-work/street_wet/grime_and_growth/ground/ 12
echo PLAN5 DONE
python3 -I proc-work/kits/weathering/ground/run_round.py pit_village_street kit:dirt,groundcracks,groundmoss,iron proc-work/street_wet/grime_and_growth/ground/rounds r5 --layers dirt,groundcracks,groundmoss,iron
echo ROUND5 DONE
python3 -I proc-work/street_wet/grime_and_growth/ground/pics_jobs.py pics_r5
echo PICS5 DONE
python3 -I proc-work/kits/weathering/ground/sheet_ground.py pit_village_street kit:dirt,groundcracks,groundmoss,iron proc-work/street_wet/grime_and_growth/ground/dial_sheet.jpg proc-work/street_wet/grime_and_growth/ground/dial_sheet_work --draw
echo SHEET5 DONE
python3 -I proc-work/street_wet/grime_and_growth/ground/st.py pit_village_street street
python3 -I proc-work/street_wet/grime_and_growth/ground/st.py pit_village_street lockout
echo SELFTEST5 DONE
python3 -I proc-work/street_wet/grime_and_growth/ground/st.py japanese_courtyard courtyard --upload
python3 -I proc-work/street_wet/grime_and_growth/ground/court.py court_r5
echo CHAIN4 DONE
