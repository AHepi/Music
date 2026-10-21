## 10. Files

Everything is under `relief_and_rubbish/study/` (about 35 MB; the film project was not touched).

* **This note**: `10 Research - sett relief and rubbish for the street.md`. **Pictures**: `pictures/` (JPEG sheets: the diagnosis, the baseline in every light, the solutions, the rubbish).
* **The one command for the test set**: `tools/run_lighting_test_set.sh` (calls `tools/b09_lighting_test_set.py` for the lists, `tools/b03_render_jobs.py` for the drawing, `tools/b05_measure_folder.py` and `tools/b04_measure_joints.py` for the measuring). `tools/b02_lighting_and_variants.py` holds the five lightings and every variant of the road (the diagnosis changes, the joint picture, the geometry, the puddle mask view).
* **Making the pictures**: `tools/b01_make_joint_mask.py` (the joint masks from the colour picture), `tools/b01b_make_soft_cavity.py` (the soft and the "closed" joint pictures), `work/joint_cavity_closed.png` (the recommended joint picture, 0.6 MB), `work/joint_cores.png` (the measuring mask picture), `work/joint_height.png` (the sharp groove picture for geometry).
* **The rubbish**: `tools/b07_probe_street_plan.py` (reads doors, wall line, lamps, props out of a street file), `tools/b10_rubbish_plan_mask.py` (draws the mask), `tools/b11_rubbish_prototype.py` (the muck layer and the scattered pieces), `work/rubbish_plan_mask.png` and `work/rubbish_plan_mask_lockout.png` (the masks), `work/plan_street.json` and `work/plan_lockout.json` (the plan).
* **The runs**: job lists `work/jobs/*.json`; `tools/b06*_make_*jobs*.py` write them; `tools/run_study_chain_*.sh` are the chains of Blender runs in the order they were done; logs in `work/logs/`; measurement files `work/r01` (baseline and diagnosis) to `work/r13` (the self-test), each with `measurements.json`; the pictures themselves are JPEGs there.
* **The note's own builder**: `tools/b13_write_note.py` with `tools/b12b_tables.py` and the text parts in `work/note_text/`.
* **Downloaded** (CC0, only to measure): `work/polyhaven_download/` (the 2k ambient occlusion and height pictures of square_cobblestone).
