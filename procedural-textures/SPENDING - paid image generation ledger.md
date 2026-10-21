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
| (none yet) | | | | | US$0.00 |

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
| 21 Oct 02:08-  | first machine (community RTX 4090) still serving the setts-and-rubbish job; the job ends by stopping it | US$0.34 an hour | |
