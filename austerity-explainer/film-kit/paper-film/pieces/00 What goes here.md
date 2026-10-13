# What goes here

`prepare_paper_pieces.py` writes each chapter's paper pieces here, one folder per chapter (for example
`austerity-chapter-1/`, made from `examples/austerity-chapter-1/cut-list.json`). The pieces of
`austerity-chapter-1/` and `inflation-chapter-2/` are kept here already made; running the tool again
on a chapter's cut list rebuilds that folder.

## Traps

- The cut list's `output_folder` decides the folder name; the chapter scene's `piecesFolder` must match it.
