"""
What this file does: the store's tools share it to read the lines a builder gives (a list of points, a curve or line-mesh
object, or a JSON file of points), to measure along them, to smooth them into the curve a wheel or a walker would take,
and to find, for many points at once, how far along the line each lies and how far to its side. It decides nothing about
where anything goes. (A name starting with '_' keeps it out of the store's list of tools.)

    import _lines
    path = _lines.Path(_lines.line_points(line)).smooth(0.05)     # a smooth curve through your points, sampled every 5 cm
    along, across, tangent = path.project(xy)                     # xy: an (n, 2) array of points seen from above
"""

import bisect
import json
import math

import bpy
import numpy
from mathutils import Vector


def _chain(mesh):
    """The vertex order of a mesh made of one line of edges (from one end to the other)."""
    if not mesh.edges:
        return list(range(len(mesh.vertices)))
    neighbours = {index: [] for index in range(len(mesh.vertices))}
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)
    ends = [index for index, near in neighbours.items() if len(near) == 1]
    start = ends[0] if ends else next(index for index, near in neighbours.items() if near)
    order, seen = [start], {start}
    while True:
        following = [index for index in neighbours[order[-1]] if index not in seen]
        if not following:
            return order
        order.append(following[0])
        seen.add(following[0])


def line_points(line):
    """World points of the line: a list of points, a curve or mesh object, or a JSON file of points."""
    if isinstance(line, str):
        with open(line) as handle:
            data = json.load(handle)
        line = data['points'] if isinstance(data, dict) else data
    if isinstance(line, bpy.types.Object):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = line.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points = [line.matrix_world @ mesh.vertices[index].co for index in _chain(mesh)]
        finally:
            evaluated.to_mesh_clear()
        return points
    return [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in line]


class Path:
    """A polyline measured along its length."""

    def __init__(self, points):
        kept = [Vector(points[0])]
        for point in points[1:]:
            if (Vector(point) - kept[-1]).length > 1e-5:
                kept.append(Vector(point))
        if len(kept) < 2:
            raise ValueError('the line needs at least two different points')
        self.points = kept
        self.lengths = [0.0]
        for a, b in zip(kept, kept[1:]):
            self.lengths.append(self.lengths[-1] + (b - a).length)
        self.total = self.lengths[-1]
        self._tree = None

    def at(self, distance):
        distance = min(max(distance, 0.0), self.total)
        index = min(bisect.bisect_right(self.lengths, distance) - 1, len(self.points) - 2)
        span = self.lengths[index + 1] - self.lengths[index]
        t = (distance - self.lengths[index]) / span if span > 0 else 0.0
        return self.points[index].lerp(self.points[index + 1], t)

    def smooth(self, spacing=0.05):
        """A new Path through the same points as a smooth curve (centripetal Catmull-Rom), sampled every `spacing`
        metres: the way a wheel or a walker would go through them, without corners."""
        points = [p.copy() for p in self.points]
        if len(points) == 2:
            count = max(2, int(math.ceil(self.total / spacing)) + 1)
            return Path([points[0].lerp(points[1], k / (count - 1)) for k in range(count)])
        padded = [points[0] * 2 - points[1]] + points + [points[-1] * 2 - points[-2]]
        samples = [points[0].copy()]
        for i in range(1, len(padded) - 2):
            p0, p1, p2, p3 = padded[i - 1], padded[i], padded[i + 1], padded[i + 2]
            t0 = 0.0
            t1 = t0 + max((p1 - p0).length, 1e-6) ** 0.5
            t2 = t1 + max((p2 - p1).length, 1e-6) ** 0.5
            t3 = t2 + max((p3 - p2).length, 1e-6) ** 0.5
            steps = max(2, int(math.ceil((p2 - p1).length / spacing)))
            for k in range(1, steps + 1):
                t = t1 + (t2 - t1) * k / steps
                a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
                a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
                a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
                b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
                b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
                samples.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
        return Path(samples)

    def arrays(self):
        """The points (n, 3), the distance along at each point (n,), and the unit way ahead at each point (n, 2)."""
        points = numpy.array([tuple(p) for p in self.points], dtype=numpy.float64)
        lengths = numpy.array(self.lengths, dtype=numpy.float64)
        ahead = numpy.zeros((len(points), 2))
        ahead[1:-1] = points[2:, :2] - points[:-2, :2]
        ahead[0] = points[1, :2] - points[0, :2]
        ahead[-1] = points[-1, :2] - points[-2, :2]
        ahead /= numpy.maximum(numpy.linalg.norm(ahead, axis=1, keepdims=True), 1e-12)
        return points, lengths, ahead

    def curvature(self):
        """How sharply the line turns at each of its points (1 / radius in metres), seen from above."""
        _, lengths, ahead = self.arrays()
        angle = numpy.unwrap(numpy.arctan2(ahead[:, 1], ahead[:, 0]))
        turning = numpy.gradient(angle, lengths) if len(lengths) > 2 else numpy.zeros(len(lengths))
        return numpy.abs(turning)

    def project(self, xy):
        """For each point (an (n, 2) array seen from above): how far along the line its nearest place lies (metres,
        below 0 or past the line's length beyond its ends), how far to the line's left it lies (metres; negative to the
        right), and the line's unit way ahead there. Best on a finely sampled Path (smooth() gives one)."""
        from scipy.spatial import cKDTree
        points, lengths, ahead = self.arrays()
        if self._tree is None:
            self._tree = cKDTree(points[:, :2])
        xy = numpy.asarray(xy, dtype=numpy.float64).reshape(-1, 2)
        _, nearest = self._tree.query(xy)
        best_along = numpy.zeros(len(xy))
        best_across = numpy.zeros(len(xy))
        best_ahead = numpy.zeros((len(xy), 2))
        best_distance = numpy.full(len(xy), numpy.inf)
        last = len(points) - 1
        for shift in (-1, 0):                                  # the segment before and the segment after the nearest point
            start = numpy.clip(nearest + shift, 0, last - 1)
            a = points[start, :2]
            b = points[start + 1, :2]
            segment = b - a
            length = numpy.maximum(numpy.linalg.norm(segment, axis=1), 1e-12)
            unit = segment / length[:, None]
            offset = xy - a
            t = numpy.sum(offset * unit, axis=1)
            low = numpy.where(start == 0, -numpy.inf, 0.0)    # beyond the line's ends the measure runs on straight
            high = numpy.where(start == last - 1, numpy.inf, length)
            t_clamped = numpy.minimum(numpy.maximum(t, low), high)
            closest = a + unit * t_clamped[:, None]
            distance = numpy.linalg.norm(xy - closest, axis=1)
            across = unit[:, 0] * offset[:, 1] - unit[:, 1] * offset[:, 0]
            along = lengths[start] + t_clamped
            better = distance < best_distance - 1e-12
            best_distance = numpy.where(better, distance, best_distance)
            best_along = numpy.where(better, along, best_along)
            best_across = numpy.where(better, across, best_across)
            best_ahead = numpy.where(better[:, None], unit, best_ahead)
        return best_along, best_across, best_ahead
