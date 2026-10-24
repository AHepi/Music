# What goes here

`prepare_paper_pieces.py` writes each chapter's paper pieces here, one folder per chapter (for example
`austerity-chapter-1/`, made from `examples/austerity-chapter-1/cut-list.json`). They are made, not
kept: delete a folder and run the tool again to rebuild it.

## Traps

- The cut list's `output_folder` decides the folder name; the chapter scene's `piecesFolder` must match it.
