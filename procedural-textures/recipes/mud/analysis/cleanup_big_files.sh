#!/bin/bash
# What this does (plain words): frees disk space at the end of the mud work by deleting picture files that can be rebuilt in a minute from the descriptions (constant roughness, metallic
# and ambient-occlusion pictures, side sheets, bigger trace lists, cropped quarters). Colour, height and normal pictures and every score file stay.
cd "$(dirname "$0")/.."
for d in outputs/R0_flat_ground outputs/R1_plus_puddle_outlines outputs/R2_plus_40_big_stones outputs/R3_plus_ruts outputs/L2_traced_ground_2000_patches outputs/L_traced_ground_5000_patches; do
  rm -f $d/roughness.png $d/metallic.png $d/ao.png $d/kind_sheet.png
done
for d in outputs/S_layout_ruts_clods outputs/M_puddle_tones_stone_faces outputs/L_final_traced_ground_plus_corrections; do rm -f $d/ao.png; done
for d in outputs_golden/*; do rm -f $d/roughness.png $d/metallic.png $d/ao.png; done
for d in outputs_golden/S_layout_ruts_clods outputs_golden/M_puddle_tones_stone_faces outputs_golden/L_traced_ground_5000_patches; do rm -f $d/height.png $d/normal.png; done
for d in variations/tile_*; do rm -f $d/roughness.png $d/metallic.png $d/ao.png $d/diff_sheet.png $d/kind_sheet.png; done
rm -f area/area_2508/roughness.png area/area_2508/metallic.png area/area_2508/ao.png
rm -rf area/quadrant_* resolution/shifted_half
rm -f resolution/size_512/{height,normal,roughness,metallic,ao}.png resolution/size_2508/{height,normal,roughness,metallic,ao}.png
rm -f transfer/snow/ao.png
rm -f analysis/ground_trace_*/patches_10000.pkl analysis/ground_trace_*/patches_20000.pkl analysis/ground_trace_*/patches_40000.pkl analysis/ground_trace_*/patches_70000.pkl analysis/ground_trace_*/tree.pkl
rm -rf outputs/geometry_route/ruts_polygons.png
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
du -sh .
