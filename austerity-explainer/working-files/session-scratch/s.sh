#!/bin/bash
# usage: s.sh manual|api "query" [n] [chars]
export BLENDER_MCP_SERVER=/home/user/work/blender-mcp/mcp-env/bin/blender-mcp BLENDER_PATH=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender BLENDER_MCP_HOST=127.0.0.1 BLENDER_MCP_PORT=9880
C="/home/user/work/blender-mcp/mcp-env/bin/python /home/user/work/paper-pop-up-film-kit/paper-film/blender/blender_mcp_call.py"
n=${3:-4}; ch=${4:-700}
$C search_${1}_docs "{\"query\": \"$2\", \"max_results\": $n}" 2>/dev/null | python3 -c "
import sys,json
t=sys.stdin.read(); i=t.find('{'); d=json.loads(t[i:])
for h in d.get('hits',[]): print('--', h['path'], '|', h.get('breadcrumb'), '\n', h['text'][:$ch].replace('\n\n','\n'))
"
