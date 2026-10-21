#!/bin/bash
# usage: _wp.sh "Page_Title" -> writes plain text to _raw/<title>.txt
t="$1"
out="_raw/$(echo "$t" | tr ' /' '__').txt"
for i in 1 2 3; do
  curl -sS -m 40 -A "ReferenceStudyBot/1.0 (personal film research)" -G "https://en.wikipedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "prop=extracts" --data-urlencode "explaintext=1" --data-urlencode "redirects=1" --data-urlencode "format=json" --data-urlencode "titles=$t" -o /tmp/_wp_tmp.json 2>/dev/null
  if python3 -I -c "
import sys,json
d=json.load(open('/tmp/_wp_tmp.json'))
for p in d['query']['pages'].values():
    print(p.get('title'));print(p.get('extract','(none)'))
" > "$out" 2>/dev/null; then break; fi
  sleep 15
done
