What this folder is: the stage check of the wet street test. `kit/` is a COPY of the film kit's stage and scene files (the film project's own folder is untouched), with my two files added
(`kit/paper-film/stage/street-wet-test.html` and `kit/paper-film/scenes/street-wet-test.js`); `kit/paper-film/node_modules` and the big glb files are links, not copies.
`run_stage_test.mjs JOBS.json OUT_FOLDER` opens the page in a hidden Chromium with software graphics (the way the film kit's own renderer does) and runs the jobs in the JSON file
(`jobs_*.json`; the last ones used were `jobs_wet4.json` for the projection pictures and `jobs_stills.json` for the map-by-map stills). Pictures and numbers are in `../work/s05/`; sheets are made by `../tools/13_stage_numbers.py`.
