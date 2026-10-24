# What this does: cuts zoomed crops of the mud reference so a person (and I) can look at the details. Analysis only.
import cv2, os, sys
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
img = cv2.imread(PROC + '/reference/mud/colour.png')
def crop(name, x, y, w, h, zoom=3):
    c = img[y:y+h, x:x+w]
    c = cv2.resize(c, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'crop_{name}.png', c)
crop('stones_cluster', 380, 960, 300, 250, 3)      # big stones and pebbles bottom
crop('puddle_edge', 500, 360, 340, 300, 3)         # a puddle with ragged edge
crop('rut', 330, 380, 300, 300, 3)                 # ruts and banks
crop('ground', 760, 300, 300, 250, 3)              # crumbly ground
