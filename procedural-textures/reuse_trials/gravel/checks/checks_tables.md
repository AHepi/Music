# What this is: the measured results of the gravel trial's half-tile and independence tests (made by checks_analyse.py)

## Half-tile test (512 dots)

| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |
|---|---|---|---|---|---|
| 1 | finished (colour) | 3.874 | 0.134 | 36.014 | 40.659 |
| 1 | pieces (colour) | 3.638 | 2.182 | 78.712 | 69.786 |
| 1 | edge_distance (height) | 0.849 | 0.002 | 30.444 | 29.963 |
| 1 | soil_mask (height) | 9.376 | 9.672 | 79.748 | 48.975 |
| 1 | facets_mask (height) | 1.521 | 0.01 | 29.305 | 36.477 |
| 2 | finished (colour) | 5.889 | 0.236 | 36.382 | 39.827 |
| 2 | pieces (colour) | 6.312 | 4.086 | 89.557 | 80.841 |
| 2 | edge_distance (height) | 1.628 | 0.002 | 39.93 | 33.091 |
| 2 | soil_mask (height) | 15.52 | 17.183 | 76.04 | 53.14 |
| 2 | facets_mask (height) | 2.731 | 0.022 | 30.729 | 36.881 |
| 2 | finished colour against itself rolled by one base tile (must differ a lot: new content, not a copy) | 36.948 | 40.228 | | |

## Independence test (320 dots)

| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside % | roughness changed % | roughness outside % |
|---|---|---|---|---|---|---|---|
| colour_and_fade | Amount 0 | 57.774 | 0.0 | 64.19 | 0.0 | 60.432 | 0.0 |
| colour_and_fade | Seed + 1 | 58.956 | 0.0 | 63.72 | 0.0 | 57.389 | 0.0 |
| facets | Amount 0 | 45.826 | 0.097 | 58.415 | 1.166 | 0.0 | 0.0 |
| facets | Seed + 1 | 32.312 | 2.433 | 40.578 | 3.606 | 0.0 | 0.0 |
| damage | Amount 0 | 6.08 | 0.0 | 7.223 | 0.018 | 5.816 | 0.0 |
| damage | Seed + 1 | 10.798 | 4.65 | 12.774 | 5.589 | 9.81 | 4.263 |
| outline_and_shadow | Amount 0 | 38.881 | 0.0 | 47.492 | 0.293 | 77.631 | 20.687 |
| outline_and_shadow | Seed + 1 | 0.64 | 0.051 | 9.426 | 0.817 | 25.379 | 14.802 |
| soil | Amount 0 | 41.018 | 0.001 | 43.05 | 0.03 | 43.478 | 2.48 |
| soil | Seed + 1 | 41.265 | 2.0 | 42.85 | 2.081 | 0.0 | 0.0 |
| gravel_layout | Seed + 1 | 94.576 | 0.0 | 96.337 | 0.0 | 79.535 | 0.0 |

(MOSS is not in the gravel stack, so no declared link is in use.)
