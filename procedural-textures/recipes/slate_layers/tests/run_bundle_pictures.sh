#!/bin/bash
# What this does: bakes one picture of each LAYOUT BUNDLE number (through the recipe's debug_view) at 1254 dots, 8 samples, then joins them
# into bundle_sheet.png. Use: tests/run_bundle_pictures.sh [SIZE]
SIZE=${1:-1254}
HERE="$(cd "$(dirname "$0")" && pwd)"
VIEWS='{"bundle_piece_colour":{"debug_view":"bundle.piece_colour"},"bundle_row":{"debug_view":"bundle.row"},"bundle_local_x":{"debug_view":"bundle.local_x"},"bundle_local_y":{"debug_view":"bundle.local_y"},"bundle_edge_distance":{"debug_view":"bundle.edge_distance"},"bundle_top_edge_distance":{"debug_view":"bundle.top_edge_distance"},"bundle_piece_width":{"debug_view":"bundle.piece_width"},"bundle_piece_height":{"debug_view":"bundle.piece_height"},"bundle_gap_mask":{"debug_view":"bundle.gap_mask"},"bundle_base_height":{"debug_view":"bundle.base_height"}}'
"$HERE/blender.sh" "$HERE/bake_tools.py" -- "$HERE/../recipe/slate_recipe.py" "$HERE/bundle_pictures" $SIZE 8 "$VIEWS" '{}' Colour 2>&1 | grep -E "Error|Traceback" 
python3 -I "$HERE/make_bundle_sheet.py" "$HERE/bundle_pictures" "$HERE/bundle_sheet.png"
