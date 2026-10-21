# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Pure numpy helpers of the where-pictures that need no Blender: the picture GRID (dots over world x and y), smoothstep, blur.
import numpy as np


class Grid:
    """A picture grid over world x and y: width x height dots of `dot` metres. Row 0 is the LOW y end; pictures are written flipped so the file's first row is the top (high y)."""

    def __init__(self, x0, x1, y0, y1, dot):
        self.x0, self.x1, self.y0, self.y1, self.dot = x0, x1, y0, y1, dot
        self.width = int(round((x1 - x0) / dot))
        self.height = int(round((y1 - y0) / dot))
        self.xs = x0 + dot * (np.arange(self.width) + 0.5)
        self.ys = y0 + dot * (np.arange(self.height) + 0.5)
        self.X, self.Y = np.meshgrid(self.xs, self.ys)

    @classmethod
    def from_settings(cls, settings, which='dot_m'):
        ground = settings.geometry['ground']
        b = ground['bounds']
        return cls(b['x'][0], b['x'][1], b['y'][0], b['y'][1], ground[which])

    def shape(self):
        return (self.height, self.width)

    def to_pixel(self, x, y):
        return (np.asarray(x) - self.x0) / self.dot - 0.5, (np.asarray(y) - self.y0) / self.dot - 0.5

    def resize_from(self, array, other):
        """Resamples an array made on another grid of the same extent onto this one (bilinear, via OpenCV)."""
        import cv2
        if array.shape[:2] == self.shape():
            return array
        return cv2.resize(array, (self.width, self.height), interpolation=cv2.INTER_LINEAR if array.dtype != bool else cv2.INTER_NEAREST)

    def meta(self):
        return dict(x=[self.x0, self.x1], y=[self.y0, self.y1], dot_m=self.dot, size=[self.width, self.height])


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(array, sigma_dots):
    import cv2
    if sigma_dots <= 0:
        return array
    k = int(sigma_dots * 6) | 1
    return cv2.GaussianBlur(array.astype(np.float32), (k, k), sigma_dots)


