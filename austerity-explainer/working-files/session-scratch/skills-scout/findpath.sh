#!/bin/bash
# usage: findpath.sh owner/repo skillname  -> prints raw URL of SKILL.md if found (status checks only, nothing saved)
repo=$1; name=$2
for br in main master; do
 for p in "skills/$name" "$name" ".claude/skills/$name" "skill/$name" "plugins/$name/skills/$name" "skills/.curated/$name" ".agents/skills/$name" "src/skills/$name" "packages/skills/$name" "plugin/skills/$name"; do
  u="https://raw.githubusercontent.com/$repo/$br/$p/SKILL.md"
  c=$(curl -s -o /dev/null -m 15 -w "%{http_code}" "$u")
  if [ "$c" = "200" ]; then echo "$u"; exit 0; fi
 done
done
echo "NOTFOUND $repo $name"
