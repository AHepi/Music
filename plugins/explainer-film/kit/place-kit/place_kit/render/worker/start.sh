#!/bin/bash
# What this does: the start command of each pay-per-second worker. It points Python at the job library and the certificate list kept on the store, then
# starts the job taker (handler.py, copied to the store as sls/handler.py) with the Python that ships inside Blender (the worker's own image is plain Ubuntu).
# The folder name 5.2 below is the version folder inside the Blender you put on the store; change it when you change the Blender version.
export PYTHONPATH=/runpod-volume/sls/site
export SSL_CERT_FILE=/runpod-volume/sls/site/certifi/cacert.pem
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE
export NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:-all}
exec /runpod-volume/blender/5.2/python/bin/python3.13 -u /runpod-volume/sls/handler.py
