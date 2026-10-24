#!/bin/bash
# What this does: the start command of each pay-per-second worker. It points Python at the job library and the certificate list kept
# on the store, then starts the job taker with the Python that ships inside Blender (the worker's own image is plain Ubuntu).
export PYTHONPATH=/runpod-volume/sls/site
export SSL_CERT_FILE=/runpod-volume/sls/site/certifi/cacert.pem
export REQUESTS_CA_BUNDLE=$SSL_CERT_FILE
export NVIDIA_DRIVER_CAPABILITIES=${NVIDIA_DRIVER_CAPABILITIES:-all}
exec /runpod-volume/blender/5.2/python/bin/python3.13 -u /runpod-volume/sls/handler.py
