#!/bin/bash
# Tester's scratch: run each calculator command with a missing file and with a broken JSON file; report tracebacks.
K=/home/user/Music/plugins/explainer-film/kit
T=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad
B=$T/broken.json
M=$T/no-such-file.json
cmds=(
"calculators/place_facts.py check BAD"
"calculators/frame_geometry.py slide --place-facts BAD --view w1"
"calculators/frame_geometry.py project --camera BAD --point 0,0,0"
"calculators/plan_shot.py --place-facts BAD --view w1"
"calculators/view_audit.py audit --place-facts BAD"
"calculators/plan_effects.py wind --place-facts BAD"
"calculators/plan_lights.py plan --place-facts BAD --view w1"
"calculators/plan_lights.py render-log BAD"
"calculators/plan_states.py plan --plan BAD"
"calculators/plan_page_timing.py check BAD"
"calculators/plan_budget.py ledger BAD"
"calculators/plan_budget.py filming BAD --scene x"
"calculators/plan_budget.py cost BAD"
"calculators/paint_request.py preflight --check BAD --facts BAD --plate BAD"
"calculators/after_painting.py check --painting BAD --plate BAD --check BAD --facts BAD --out-folder /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/ap"
"narration-tools/lint_script.py before BAD"
"narration-tools/sound_gates.py length BAD --expected 3"
"paper-film/tools/camera_audit.py BAD"
"calculators/settings.py get frame.nothing"
)
for c in "${cmds[@]}"; do
  for which in missing broken; do
    f=$M; [ $which = broken ] && f=$B
    cmd=${c//BAD/$f}
    out=$(cd $K && timeout 60 python3 $cmd 2>&1); code=$?
    tb=$(echo "$out" | grep -c 'Traceback')
    last=$(echo "$out" | grep -v '^\s*$' | tail -1 | cut -c1-150)
    printf '%-60s %-8s exit %-3s traceback %s | %s\n' "${c%% *} ${c#* }" "$which" "$code" "$tb" "$last" | cut -c1-260
  done
done
for which in missing broken; do
  f=$M; [ $which = broken ] && f=$B
  out=$(cd $K && node paper-film/tools/check_page_layout.mjs $f 2>&1); code=$?
  printf 'check_page_layout.mjs %-8s exit %s | %s\n' $which $code "$(echo "$out" | grep -v '^\s*$' | tail -1 | cut -c1-150)"
done
