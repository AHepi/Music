# What this is: the measured results of the metal trial's half-tile and independence tests (made by checks_analyse.py)

## Half-tile test (512 dots)

| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |
|---|---|---|---|---|---|
| 1 | finished (colour) | 2.601 | 0.024 | 21.013 | 15.307 |
| 1 | pieces (colour) | 1.44 | 0.525 | 16.764 | 12.153 |
| 1 | edge_distance (height) | 0.667 | 0.0 | 44.922 | 52.648 |
| 1 | rivets_mask (height) | 0.448 | 0.418 | 8.891 | 4.293 |
| 2 | finished (colour) | 4.487 | 0.126 | 24.82 | 19.119 |
| 2 | pieces (colour) | 2.048 | 1.224 | 28.476 | 23.484 |
| 2 | edge_distance (height) | 1.417 | 0.0 | 78.175 | 57.734 |
| 2 | rivets_mask (height) | 0.903 | 0.967 | 16.208 | 7.84 |
| 2 | finished colour against itself rolled by one base tile (must differ a lot: new content, not a copy) | 26.418 | 20.43 | | |

## Independence test (320 dots)

| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside % | roughness changed % | roughness outside % |
|---|---|---|---|---|---|---|---|
| colour_and_fade | Amount 0 | 58.411 | 0.0 | 72.679 | 0.0 | 79.823 | 0.0 |
| colour_and_fade | Seed + 1 | 66.769 | 0.0 | 73.75 | 0.0 | 88.036 | 0.0 |
| damage | Amount 0 | 20.857 | 0.0 | 21.697 | 0.001 | 25.2 | 0.0 |
| damage | Seed + 1 | 34.648 | 16.426 | 35.541 | 16.54 | 37.863 | 17.26 |
| moss | Amount 0 | 26.641 | 0.0 | 26.331 | 0.021 | 27.483 | 0.0 |
| moss | Seed + 1 | 38.642 | 13.234 | 39.041 | 13.12 | 30.612 | 13.733 |
| outline_and_shadow | Amount 0 | 10.274 | 0.0 | 12.224 | 0.097 | 8.909 | 0.0 |
| outline_and_shadow | Seed + 1 | 4.438 | 0.324 | 10.804 | 0.852 | 3.381 | 0.397 |
| edge_light | Amount 0 | 6.917 | 0.0 | 7.296 | 0.034 | 1.459 | 0.0 |
| edge_light | Seed + 1 | 2.643 | 0.365 | 3.572 | 0.506 | 1.086 | 0.169 |
| rivets | Amount 0 | 3.639 | 0.0 | 3.632 | 0.002 | 3.032 | 0.0 |
| rivets | Seed + 1 | 5.452 | 1.84 | 5.487 | 1.859 | 4.297 | 1.534 |
| metal_layout | Seed + 1 | 97.602 | 0.0 | 98.998 | 0.0 | 95.043 | 0.0 |

(DAMAGE may change MOSS through the declared link MOSS <- Damage Mask, so its outside-mask count may include MOSS dots: they are allowed and counted inside. The layout feeds everything.)
