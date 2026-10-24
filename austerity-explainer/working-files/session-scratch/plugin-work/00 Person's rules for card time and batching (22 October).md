# The person's rules for card time and batching (22 October, about 21:50 UTC)

What this file is: the person's own words on how helpers should use the rented cards. These rules go into the plugin as a follow-up step after
the "plugin-surfaces-and-wear" workflow, and they apply to the forest village test.

* The question that led to it: "Why did it cost $10? That's really expensive for a few photos". The answer: the final pictures cost about
  5 cents; the rest was helpers trying things out one change at a time, with no limit on card time.
* My proposal, which the person liked ("Great idea!"): a card-time allowance per helper, small and quick test pictures, the scene built once and
  saved, full-size pictures drawn once at the end, and the same rule in the plugin.
* The person's words: "And batch them with workers. Do one full sweep of changes, then look. Instead of one small change, then check. Maybe
  even batch according to variations. So maybe 10 variations that are measurably different for each asset change. That way, they can test
  multiple different types of changes at once."
* What that means in practice:
  - make every change in one sweep, then draw and look once;
  - for each change to a thing, draw about 10 versions in one batch;
  - the versions must be measurably different from each other (their settings, and the pictures they give);
  - spread the batch over the workers (up to 3 cards at once);
  - show the results as one sheet with the measures, then pick a version or combine the best ones.
* Village test cap: about US$3 of card time in total.

## Later rule (23 October, about 04:10 UTC)
* The person said: "I'm thinking you should use Opus for the plugin work. So switch to Opus 5.5 as subagents for now".
* So helpers that write or check the plugin now run on Opus 5.5 at xhigh.
* The blind newcomers and the village builder stay on Sonnet, because they stand for the smaller model the plugin is for, and the person's
  test is "Sonnet needs to use ...".
* The batching step was stopped part-done (its Sonnet attempt had run about 50 minutes; its changes are kept in git) and restarted on Opus.
* The lessons audit (finished) found about 370 lessons: about 210 fully carried, about 90 partly, about 70 missing, and 40 that matter.
  Its result is in plugin-work/lessons_audit_result.json. The next step adds those 40.

## Standing rule (23 October, about 16:30 UTC)
* The person said: "Also for future reference, every new set that uses different tools needs to update the plugin."
* Recorded in the repository's new CLAUDE.md and as Decisions.md items 45-48 (saved and pushed, commit 7410b89).
* TO DO when the three-run job (Opus update, Sonnet rebuild, Opus verify) finishes: add the same rule to the plugin's own house rules
  (skills/make-explainer-film/house-rules.md), so a model using the plugin elsewhere keeps the plugin up to date too.
