# Spending ledger - paid image generation (fal) in the procedural-textures work

What this file is: every paid call made by the helpers in this work, in one place, and the person's spending rule. Helpers add a row for each paid call
(date and time, job, model, settings, price by the price list, request id) and keep the running total.

## The person's rule (20 October, about 20:00)
"Just do it. $20 budget, ask free. Over that, start asking." Meaning: paid image generation that serves the work the person asked for may be spent without
asking, up to US$20.00 in total from this point; before any call that would take the total over US$20.00, stop and ask the person.
Helpers still look up the price before every paid call and never repeat a call just to get a nicer picture without a reason written down.

## Before the budget (already spent, not counted against the US$20)
| when | job | calls | price by the price list |
|---|---|---|---|
| 20 Oct 13:15-14:30 | generated mask stamps test (fal-ai/flux/dev, 6 pictures) | 6 | US$0.354 (at most 0.45) |
| 20 Oct 19:02 | wet street painter test (blackforestlabs/flux-3/edit-image, 2k) | 1 | US$0.197 to 0.277 |

## Against the US$20 budget
| when | job | model and settings | price | request id | running total |
|---|---|---|---|---|---|
| 2026-10-21 06:38 | wet street painter round 2, FRONT PAINTING: the one repaint of the new full-size wet lockout plate (step "the front painting"); sent once, no repeat | blackforestlabs/flux-3/edit-image; resolution 2k, aspect_ratio auto, output_format png, safety_tolerance 2, prompt expansion off; image 1 = new wet plate shrunk to 810x1440, image 2 = the series style picture 504x896 (same as first test) | US$0.048 per megapixel (price list looked up 06:37): output about 4.1 MP = US$0.197; plus both pictures sent, 1.62 MP = US$0.078, if they are charged: worst case US$0.277 | 01a15d2e-ad95-7d40-8c3c-421e2f20da8b (submitted 06:39 UTC, finished 06:41 UTC first time, no error; returned 1520x2702 = 4.107 MP, so output US$0.197) | US$0.28 worst case / US$0.20 best case (fal shows no exact charge) |
| 2026-10-21 07:03 UTC | wet street painter round 2, WET BEHIND PAINTING: the one repaint of the props-free wet lockout plate, in the hand of the front painting (step "the wet behind painting"); sent once, no repeat | blackforestlabs/flux-3/edit-image; resolution 2k, aspect_ratio auto, output_format png, safety_tolerance 2, prompt expansion off; image 1 = props-free wet plate shrunk to 810x1440, image 2 = the finished front painting (front_painting_final.png) shrunk to 504x896 | US$0.048 per megapixel (price list looked up just before the call, same as before): output about 4.1 MP = US$0.197; plus both pictures sent, 1.62 MP = US$0.078, if they are charged: worst case US$0.277 | 01a15d46-0135-7ec1-a086-d80f9d964f6e (finished 07:05 UTC first time, no error; returned 1520x2702 = 4.107 MP, so output US$0.197) | US$0.55 worst case / US$0.39 best case for the whole round 2 so far (front painting 0.28 / 0.20 + this 0.28 / 0.20); under the US$3.00 limit of this job |
| 2026-10-21 18:31 UTC | grime-kit painter test (weathering kit: grime, cracks, stains, weeds and moss): the ONE repaint of the kit's final wet lockout plate (step "Paint", limit US$1.00 for the step); sent once, no repeat | blackforestlabs/flux-3/edit-image; resolution 2k, aspect_ratio auto, output_format png, safety_tolerance 2, prompt expansion off (same as round 2); image 1 = street_wet/grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png shrunk to 810x1440, image 2 = the series style picture 504x896 (byte for byte round 2's); brief = round 2's front-painting brief plus one sentence (keep the soot grime, run-off streaks, stains, cracks, weeds and moss where image 1 has them, at the same size and strength, painted in image 2's hand) | US$0.048 per megapixel (price list looked up 18:30 UTC with fal's price tool, unchanged): output about 4.1 MP = US$0.197; plus both pictures sent, 1.62 MP = US$0.078, if they are charged: worst case US$0.277 | 01a15fbb-34d2-7eb2-b49d-95f10178b2f3 (submitted 18:31 UTC, finished by 18:32 UTC first time, no error; returned 1520x2702 = 4.107 MP, so output US$0.197; one call, no repeat) | US$0.83 worst case / US$0.59 best case (rows above 0.55 / 0.39 + this 0.28 / 0.20); the person's US$20 budget is far from reached |

## RunPod rented render machine (budget first US$5.00 "to get started"; then on 21 October about 04:00: "Don't worry about runpod budget. Just find a workflow that works")
| when (UTC) | what | price | running total |
|---|---|---|---|
| 21 Oct 02:08 | started: one RTX 4090, community cloud, 60 GB disk, job server + Blender 5.2.2 (machine id kept privately in ~/.runpod) | US$0.34 an hour | |
| 21 Oct 02:31 | set-up and tests done (22 minutes) | | about US$0.13 |
| 21 Oct 02:45 | the setts-and-rubbish job moved onto it | | |
| 21 Oct 02:58 | permanent store: 30 GB network volume "blender-render-cache" in EU-RO-1 (kept between machines) | about US$0.07 a day (US$2.10 a month) | |
| 21 Oct 03:00-03:20 | cached set-up: two machines (RTX 4090, secure cloud) that failed to start properly because of two set-up mistakes of mine, ended | US$0.89 an hour, about 35 minutes in all | about US$0.52 |
| 21 Oct 03:20-03:40 | cached set-up: working machine (RTX 4090, secure), tests and uploads, then left to end itself after 15 idle minutes | US$0.89 an hour | about US$0.30 |
| 21 Oct 03:40-04:10 | route tests on the Romania store (RTX 2000 Ada, RTX 4090) and two community starts that failed on the Blender download (fixed) | US$0.27-0.89 an hour | about US$0.35 |
| 21 Oct 04:15 | second permanent store: 30 GB network volume in EUR-IS-1 (Iceland) | about US$0.07 a day (US$2.10 a month) | |
| 21 Oct 04:29-04:41 | Iceland store test machine (RTX 4090, secure), ended by me when the test was done | US$0.89 an hour | about US$0.18 |
| 21 Oct 04:34-04:40 | community route test machine (RTX A5000, no store), ended by me | about US$0.27 an hour | about US$0.03 |
| 21 Oct 04:40 | RunPod's own bill for machines so far today: US$1.13 (it lags about an hour; the newest machines are not in it yet) | | about US$1.6-1.8 in all |
| 21 Oct 02:08-05:10 | first machine (community RTX 4090) served the setts-and-rubbish job; the job stopped it at the end and I ended it for good at 05:12 (a stopped machine still pays for its disk) | US$0.34 an hour, about 3 hours | about US$1.00 |
| 21 Oct 05:40 | safety check: RunPod's bill for machines today US$1.75 (lags about an hour); one machine running (RTX 4090 on the Romania store, started 05:39 for the painter round 2 and the Blender-skills try-out); it ends itself after 30 idle minutes | US$0.89 an hour while running | |
| 21 Oct 05:39-08:38+ | that machine has stayed busy since: painter round 2 (plates, stage), the Blender-skills try-outs, the weathering kit and the EEVEE-and-Cycles comparison; still running at 08:38, ends itself 30 minutes after the last job | US$0.89 an hour | about US$2.65 so far |
| 21 Oct 08:38 | RunPod's own bill for machines today: US$3.85 (lags about an hour); the two stores so far US$0.03 | | |
| 21 Oct 05:39-18:44 | the same machine served every job until the end (EEVEE and Cycles comparison, the wet lockout checks, the weathering kit with its fix round); ended by me at 18:44 when all jobs were done, as you asked | US$0.89 an hour, about 13 hours | about US$11.60 |
| 21 Oct 18:44 | RunPod's own bill for machines today: US$12.85 (lags about an hour); stores so far US$0.09; no machine running | | |


## Seen in fal's history but not from this work
The round 2 checker found four fal calls on 21 Oct 03:05-03:18 UTC (three Nano Banana Pro edits and one Alligator video, about US$0.96 by the price list) that no helper in this work made; they look like another project's. Not counted here.
