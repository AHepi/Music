# What this is: the measured results of the brick trial's half-tile and independence tests (made by checks_analyse.py)

## Half-tile test (512 dots)

| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |
|---|---|---|---|---|---|
| 1 | finished (colour) | 2.921 | 0.027 | 32.395 | 30.892 |
| 1 | pieces (colour) | 1.024 | 0.31 | 23.883 | 20.363 |
| 1 | edge_distance (height) | 0.816 | 0.0 | 57.222 | 67.392 |
| 1 | grime_mask (height) | 6.0 | 5.701 | 67.126 | 41.195 |
| 2 | finished (colour) | 4.663 | 0.143 | 36.215 | 35.97 |
| 2 | pieces (colour) | 1.383 | 0.492 | 46.736 | 39.043 |
| 2 | edge_distance (height) | 1.624 | 0.0 | 94.02 | 77.853 |
| 2 | grime_mask (height) | 10.188 | 10.64 | 70.858 | 47.655 |
| 2 | finished colour against itself rolled by one base tile (must differ a lot: new content, not a copy) | 29.002 | 24.828 | | |

## Independence test (320 dots)

| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside % | roughness changed % | roughness outside % |
|---|---|---|---|---|---|---|---|
| colour_and_fade | Amount 0 | 62.803 | 0.0 | 66.971 | 0.0 | 69.5 | 0.0 |
| colour_and_fade | Seed + 1 | 63.581 | 0.0 | 67.746 | 0.0 | 71.111 | 0.0 |
| damage | Amount 0 | 9.284 | 0.0 | 10.753 | 0.004 | 11.14 | 0.0 |
| damage | Seed + 1 | 15.098 | 6.2 | 17.382 | 7.031 | 17.11 | 7.225 |
| moss | Amount 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| moss | Seed + 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| outline_and_shadow | Amount 0 | 36.51 | 0.0 | 38.117 | 0.374 | 38.621 | 0.0 |
| outline_and_shadow | Seed + 1 | 12.9 | 0.824 | 18.781 | 1.749 | 8.749 | 0.572 |
| grime | Amount 0 | 33.756 | 0.0 | 34.86 | 0.039 | 32.273 | 0.0 |
| grime | Seed + 1 | 47.108 | 14.545 | 48.676 | 15.048 | 43.445 | 14.112 |
| brick_layout | Seed + 1 | 79.649 | 0.0 | 81.63 | 0.0 | 77.622 | 0.0 |

(MOSS is switched off in the brick settings, so its rows must be 0. DAMAGE may change MOSS through the declared link; with MOSS off it cannot.)
