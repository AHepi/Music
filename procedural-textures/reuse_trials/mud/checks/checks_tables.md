# What this is: the measured results of the mud trial's half-tile and independence tests (made by checks_analyse.py)

## Half-tile test (512 dots)

| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |
|---|---|---|---|---|---|
| 1 | finished (colour) | 3.667 | 0.864 | 30.978 | 31.812 |
| 1 | pieces (colour) | 1.556 | 0.637 | 41.231 | 35.261 |
| 1 | relief (height) | 0.223 | 0.0 | 8.151 | 8.054 |
| 1 | ruts_mask (height) | 0.936 | 0.893 | 26.581 | 11.896 |
| 1 | moss_mask (height) | 0.903 | 1.295 | 23.666 | 10.896 |
| 1 | stones_mask (height) | 1.219 | 1.778 | 35.785 | 16.702 |
| 2 | finished (colour) | 4.61 | 0.788 | 33.017 | 35.162 |
| 2 | pieces (colour) | 2.462 | 1.271 | 73.627 | 63.742 |
| 2 | relief (height) | 0.457 | 0.0 | 12.897 | 12.911 |
| 2 | ruts_mask (height) | 1.806 | 2.084 | 47.747 | 21.61 |
| 2 | moss_mask (height) | 1.704 | 2.464 | 36.583 | 17.366 |
| 2 | stones_mask (height) | 2.383 | 3.457 | 40.931 | 20.848 |
| 2 | finished colour against itself rolled by one base tile (must differ a lot: new content, not a copy) | 36.825 | 42.484 | | |

## Independence test (320 dots)

| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside % | roughness changed % | roughness outside % |
|---|---|---|---|---|---|---|---|
| colour_and_fade | Amount 0 | 56.813 | 0.0 | 58.951 | 0.0 | 89.763 | 0.0 |
| colour_and_fade | Seed + 1 | 56.136 | 0.0 | 58.726 | 0.0 | 93.638 | 0.0 |
| ruts | Amount 0 | 25.4 | 0.0 | 26.258 | 0.005 | 30.475 | 0.0 |
| ruts | Seed + 1 | 41.121 | 0.0 | 42.375 | 0.012 | 42.017 | 0.0 |
| moss | Amount 0 | 12.81 | 0.0 | 12.727 | 0.003 | 13.652 | 0.0 |
| moss | Seed + 1 | 7.216 | 0.0 | 7.286 | 0.001 | 0.405 | 0.0 |
| damage | Amount 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| damage | Seed + 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| stones | Amount 0 | 11.319 | 0.0 | 11.438 | 0.007 | 10.999 | 0.0 |
| stones | Seed + 1 | 19.435 | 0.0 | 19.6 | 0.013 | 18.241 | 0.0 |
| outline_and_shadow | Amount 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| outline_and_shadow | Seed + 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| mud_layout | Seed + 1 | 70.506 | 0.0 | 72.74 | 0.0 | 94.399 | 0.0 |

(DAMAGE and OUTLINE AND SHADOW are switched off in the mud settings, so their rows must be 0 and prove little. MOSS reads DAMAGE only through the declared link, and the link has no effect with Damage Avoid and Damage Attract at 0. The layout feeds every layer, so its row changes everything.)
