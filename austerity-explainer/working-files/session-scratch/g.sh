#!/bin/bash
# usage: g.sh "regex" [maxlines]
pat="$1"; max="${2:-8}"
echo "=== $pat"
grep -rIn -i -E "$pat" /home/user/Music/plugins/explainer-film --include=*.md --include=*.py --include=*.js --include=*.mjs --include=*.sh --include=*.txt --include=*.json 2>/dev/null | grep -v "/tests/fixtures/" | cut -c1-260 | head -n "$max"
