# What this does (plain words): builds the in-between descriptions for the rate-distortion table (analysis/build_rd_descriptions.py), then bakes and scores each one
# (layer A, layer B, and layout + traced patches at 16, 32, 128 and 256 KB). Run from anywhere; it changes into the recipe folder itself.
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/metal
python3 -I analysis/build_rd_descriptions.py
for n in layerA layerB R16k R32k R128k R256k; do python3 -I generator/bake_and_score.py $n --samples 8 2>&1 | grep -E "tier|groups" | cut -c1-260; done
