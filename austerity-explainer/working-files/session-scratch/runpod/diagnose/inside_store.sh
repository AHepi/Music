# What this does: run on an ordinary rented machine that has the Romania store at /workspace. Checks that the pay-per-second
# worker's files are intact and that its job taker starts and answers a test job. Prints no keys.
echo "== start script"; cat /workspace/sls/start.sh
echo "== files"; ls -la /workspace/sls | head; ls /workspace/sls/site | wc -l; ls -la /workspace/blender/5.2/python/bin/python3.13
echo "== newest job logs"; ls -lt --time-style=+%H:%M /workspace/sls/job_logs | head -6
echo "== store use (top folders)"; timeout 120 du -sh /workspace/* 2>/dev/null | sort -h | tail -8
echo "== handler test"
cd /tmp && PYTHONPATH=/workspace/sls/site SSL_CERT_FILE=/workspace/sls/site/certifi/cacert.pem timeout 120 \
  /workspace/blender/5.2/python/bin/python3.13 -u -c "import sys; sys.path.insert(0, '/workspace/sls'); import handler, runpod; print('runpod', runpod.__version__); runpod.serverless.start({'handler': handler.handle_job})" \
  --test_input '{"input": {"op": "info", "path": "/workspace/sls/start.sh"}}' 2>&1 | tail -15
echo "== done"
