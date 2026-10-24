#!/bin/bash
sed -i 's/ out \([a-z0-9]*\) house/ out \1_house house/' "$(dirname "$0")/run.sh"
