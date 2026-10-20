## A. Change MOSS, look at the finished picture

| what was changed | moss dots before % | moss dots after % | colour changed % | colour changed outside moss % | height changed % | height outside moss % | roughness changed % | roughness outside moss % |
|---|---|---|---|---|---|---|---|---|
| moss Amount 0 | 16.04 | 0.0 | 13.146 | 0.0 | 14.471 | 0.0 | 15.137 | 0.0 |
| moss Seed + 1 | 16.04 | 20.47 | 25.654 | 0.0 | 27.723 | 0.0 | 26.959 | 0.0 |
| moss Coverage 0.5 | 16.04 | 43.66 | 34.067 | 0.0 | 32.253 | 0.0 | 32.876 | 0.0 |

## B. Change ANOTHER layer, look at what MOSS makes (its own mask and colour, baked alone)

| what was changed | allowed to reach moss through | moss mask dots changed % | moss colour dots changed % | moss mask changed outside damage % |
|---|---|---|---|---|
| colour_and_fade seed + 1 | nothing | 0.0 | 0.0 | - |
| outline_and_shadow seed + 1 | nothing | 0.0 | 0.0 | - |
| damage seed + 1 | the declared link (damage mask) | 3.004 | 0.064 | 0.029 |
| damage amount 0 | the declared link (damage mask) | 1.94 | 0.034 | 0.022 |
| layout seed + 1 | the layout bundle (all layers read it) | 29.794 | 24.059 | - |
