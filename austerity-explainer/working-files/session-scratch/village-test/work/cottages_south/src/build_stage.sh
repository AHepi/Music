#!/bin/bash
cd "$(dirname "$0")"
OUT=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_cottages_south.py
cat p1_core.py p2_helpers.py p3_frame.py p4_cottage_c.py $(ls p5_*.py 2>/dev/null) p6_apply.py > "$OUT"
python3 -c "import ast,sys;ast.parse(open('$OUT').read())" && echo "stage written: $(wc -l < $OUT) lines"
