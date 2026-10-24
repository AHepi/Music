# What goes here

`film-chapter.sh` writes each chapter's filmed pages here (`<chapter>-chunks/`) and the joined silent film
(`<chapter>-silent.mp4`).

## Traps

- To film one page again, delete its chunk file and run `film-chapter.sh` again; the other pages are kept.
- A changed page edge (a re-recorded page) gives new chunk names: delete the whole chunks folder.
