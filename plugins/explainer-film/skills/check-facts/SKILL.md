---
name: check-facts
description: Fact-check a narration script and its on-screen words with independent, skeptical helpers who try to prove every claim wrong from fresh primary sources, then settle disagreements and list fixes. Use before recording, and again when the on-screen words are final.
---

# Check the facts

Run the bundled workflow (it splits the script into topic groups, sends one skeptical checker per
group, then a final reviewer settles disagreements and looks for uncovered claims):

```
Workflow({ name: "explainer-film:verify-facts", args: {
  script: "/abs/path/NN Script - chapter.md",
  today: "12 October 2026",
  ledger: "/abs/path/NN Research - chapter.md",          // optional
  onScreen: "/abs/path/film-kit/paper-film/scenes/<chapter>/page-*.js",   // optional, once pages exist
  audience: "a general New Zealand audience",            // optional
  effort: "medium"                                       // match the user's wish
} })
```

If workflows are not available, do the same by hand with the Agent tool: one agent per topic group
(at most 7) with the prompt in `${CLAUDE_PLUGIN_ROOT}/workflows/verify-facts.js` (`verifyPrompt`),
then one final reviewer agent given all their verdicts.

## Then

- Apply must-fix and should-fix items. Prefer changing on-screen words; a spoken change means
  re-recording that page and redoing the timing, mix and filming after it (tell the user the cost).
- Write the result into the research ledger as a new section (claim, verdict, what the sources say,
  sources, change made) and keep the raw JSON next to it.
- Tell the user in plain words: what was checked, what holds, what changed, what is still unverified,
  and which figures will go out of date soon (next statistics release, next central bank decision).

## What the checkers caught in chapter 2 (so you know what to expect)

- A ratio label contradicting its own numbers ($2.90 → $11.65 is 4.02 times: "×4", not "nearly ×4").
- "+25%" on screen where the source says "up to 25%": show "UP TO +25%".
- "Lowest since records began" where the records start in 1986: show "LOWEST SINCE 1986".
- A hundred-dot panel with exactly one empty dot for "under 1%" (0.95%): draw the last dot nearly
  empty.
