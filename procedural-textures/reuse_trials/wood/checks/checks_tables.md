# What this is: the measured results of the wood trial's half-tile and switch-off tests (made by checks_analyse.py)

## Half-tile test (512 dots)

| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |
|---|---|---|---|---|---|
| 1 | finished (colour) | 5.164 | 0.163 | 34.601 | 33.639 |
| 1 | pieces (colour) | 0.848 | 0.274 | 11.238 | 7.302 |
| 1 | edge_distance (height) | 0.517 | 0.0 | 37.434 | 44.542 |
| 1 | cracks_mask (height) | 0.736 | 0.45 | 10.025 | 6.837 |
| 1 | knots_mask (height) | 0.282 | 0.011 | 3.397 | 3.05 |
| 1 | grain_mask (height) | 12.488 | 4.744 | 42.585 | 43.044 |
| 2 | finished (colour) | 7.648 | 0.453 | 33.297 | 30.853 |
| 2 | finished colour against itself rolled by one base tile (a copy would give 0) | 31.335 | 27.261 | | |

## Switch-off test (320 dots, Amount 0)

| layer switched off | colour changed % | colour changed outside own mask % | height changed % | height changed outside own mask % | own mask covers % |
|---|---|---|---|---|---|
| colour_and_fade | 79.244 | 0.0 | 93.621 | 0.0 | 95.63 |
| grain | 52.359 | 0.008 | 54.581 | 0.11 | 65.4 |
| moss | 19.755 | 0.0 | 20.051 | 0.011 | 21.08 |
| damage | 1.036 | 0.0 | 1.194 | 0.001 | 1.44 |
| cracks | 4.473 | 0.003 | 4.627 | 0.071 | 4.71 |
| knots | 8.293 | 0.0 | 9.275 | 0.035 | 9.87 |
| outline_and_shadow | 8.703 | 0.0 | 9.892 | 0.346 | 9.74 |

