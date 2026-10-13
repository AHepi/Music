# Music

**What this is:** the working folder for the user's film projects.

- `austerity-explainer/`: the narrated paper pop-up explainer on where austerity came from, from
  Clara E. Mattei's *The Capital Order* (2022). Start with
  `austerity-explainer/project-notes/Austerity explainer - project story.md`.
  - Chapter 1 ("Where austerity came from") is finished; its project notes, research, scripts and
    rules are copied here from the "17 Chapter 1" zip.
  - Chapter 2 ("What really causes inflation") is in `austerity-explainer/chapter-2-inflation/`.
  - The film kit, with everything needed to make or remake either chapter (every painting, paper
    piece and model, the tools, chapter 1's recordings, both chapters as worked examples), is in
    `austerity-explainer/film-kit/`. Start with its `00 START HERE.md`.
- `plugins/explainer-film/`: the method as a Claude Code plugin, so another model can make the next
  chapter. Install with `/plugin marketplace add AHepi/Music` then
  `/plugin install explainer-film@ahepi-music`.

## Traps

- This repository is public. The soundtrack "Tension and Gravity.mp3" is not stored here, so the
  track can't be downloaded on its own: copy it into `austerity-explainer/film-kit/assets/soundtrack/`
  before mixing a new chapter.
- The full-quality film files (about 800 MB each) are too big for GitHub; the sendable copies are in
  each chapter's `deliver/` folder, and the full-quality ones can be filmed again from the kit.
