# What goes here

`prepare_paper_pieces.py` writes each chapter's paper pieces here, one folder per chapter (for example
`austerity-chapter-1/`, made from `examples/austerity-chapter-1/cut-list.json` and the chapter's paintings).
The plugin's kit ships no pieces (they are pictures, and the plugin stays small): make them from your own
paintings, or copy a finished chapter's folder from the austerity project's film kit
(`austerity-explainer/film-kit/paper-film/pieces/`).

## Traps

- The cut list's `output_folder` decides the folder name; the chapter scene's `piecesFolder` must match it.
