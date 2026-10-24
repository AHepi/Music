

# ------------------------------------------------------------------ materials (our own, with a small picture so the surface pass keeps them)
IMAGE_NAME = 'Cottages south variation'


def variation_image():
    """A small soft grey picture (values 0.45 to 1.0) that varies the colour and the roughness a little across every object. Colour space is set BEFORE the pixels are written."""
    size = 96
    img = bpy.data.images.get(IMAGE_NAME)
    if img is None or img.size[0] != size:
        if img is not None:
            bpy.data.images.remove(img)
        img = bpy.data.images.new(IMAGE_NAME, size, size, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rng = np.random.default_rng(5)
    f = np.fft.fft2(rng.normal(size=(size, size)))
    kx = np.fft.fftfreq(size)[:, None]
    ky = np.fft.fftfreq(size)[None, :]
    k = np.sqrt(kx * kx + ky * ky)
    k[0, 0] = 1.0
    field = np.real(np.fft.ifft2(f / (k ** 1.1)))
    field = (field - field.min()) / (field.max() - field.min())
    values = 0.45 + 0.55 * field
    pixels = np.ones((size, size, 4), dtype=np.float32)
    pixels[..., 0] = pixels[..., 1] = pixels[..., 2] = values
    img.pixels.foreach_set(pixels.ravel())
    img.update()
    try:
        img.pack()
    except RuntimeError:
        pass
    return img


def make_material(name, rough_low=0.7, rough_high=0.95, displace=None):
    """Colour = the mesh's Col layer times a gentle variation read from the small picture (object space, so no two objects match); roughness varies with the same picture."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    attr = tree.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'Col'
    attr.attribute_type = 'GEOMETRY'
    coord = tree.nodes.new('ShaderNodeTexCoord')
    mapping = tree.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (0.9, 0.9, 0.9)
    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.image = variation_image()
    tex.interpolation = 'Linear'
    tex.projection = 'BOX'
    tex.projection_blend = 0.3
    sep = tree.nodes.new('ShaderNodeSeparateColor')
    vary = tree.nodes.new('ShaderNodeMapRange')
    vary.inputs['From Min'].default_value = 0.45
    vary.inputs['From Max'].default_value = 1.0
    vary.inputs['To Min'].default_value = 0.9
    vary.inputs['To Max'].default_value = 1.1
    scale = tree.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    rough = tree.nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value = 0.45
    rough.inputs['From Max'].default_value = 1.0
    rough.inputs['To Min'].default_value = rough_low
    rough.inputs['To Max'].default_value = rough_high
    L = tree.links.new
    L(coord.outputs['Object'], mapping.inputs['Vector'])
    L(mapping.outputs['Vector'], tex.inputs['Vector'])
    L(tex.outputs['Color'], sep.inputs['Color'])
    L(sep.outputs['Red'], vary.inputs['Value'])
    L(sep.outputs['Red'], rough.inputs['Value'])
    L(attr.outputs['Color'], scale.inputs[0])
    L(vary.outputs['Result'], scale.inputs['Scale'])
    L(scale.outputs['Vector'], bsdf.inputs['Base Color'])
    L(rough.outputs['Result'], bsdf.inputs['Roughness'])
    L(bsdf.outputs['BSDF'], out.inputs['Surface'])
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.25
    except KeyError:
        pass
    out.is_active_output = True
    if displace:
        # real displacement for the thatch (the role asks for it): the picture read at a finer tile, mid level 0.5, scale = the true depth in metres
        from place_kit.surfaces import displacement as disp
        map2 = tree.nodes.new('ShaderNodeMapping')
        map2.inputs['Scale'].default_value = (4.5, 4.5, 4.5)
        tex2 = tree.nodes.new('ShaderNodeTexImage')
        tex2.image = tex.image
        tex2.projection = 'BOX'
        tex2.projection_blend = 0.3
        sep2 = tree.nodes.new('ShaderNodeSeparateColor')
        L(coord.outputs['Object'], map2.inputs['Vector'])
        L(map2.outputs['Vector'], tex2.inputs['Vector'])
        L(tex2.outputs['Color'], sep2.inputs['Color'])
        disp.set_displacement(mat, sep2.outputs['Red'], displace, tree)
    mat['cs_made'] = 1
    return mat


# ------------------------------------------------------------------ the parts registry
class Parts:
    """The objects of the part, by key: each has an accumulator, a name, a role (its role is given as it is made) and a flag for seating on the ground."""

    def __init__(self):
        self.d = {}
        self.order = []

    def acc(self, key, name, role, smooth=False, seat=False):
        if key not in self.d:
            self.d[key] = dict(acc=Acc(smooth=smooth), name=name, role=role, seat=seat)
            self.order.append(key)
        return self.d[key]['acc']


def wbox(wall, u0, u1, w0, w1, z0, z1):
    """A box in a wall's own frame (u along, w across, z up) as ONE closed solid."""
    pts = [wall.P(u, w, z) for (u, w, z) in ((u0, w0, z0), (u1, w0, z0), (u1, w1, z0), (u0, w1, z0), (u0, w0, z1), (u1, w0, z1), (u1, w1, z1), (u0, w1, z1))]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array(pts, float), F


def post_solid(wall, u, w, a, b, z0, z1, lean=(0.0, 0.0), bow=(0.0, 0.0), twist=0.0, taper=1.0, topz=None):
    """A post or stud in a wall's frame: three rings (foot, middle, head), leaning by `lean` (metres of drift at the head), bowing by `bow` at the middle, turned by `twist` radians at the head
    and narrowing by `taper`. topz(world xy corners) may give each head corner its own height (a head cut to the slope of a rafter)."""
    rings = []
    for t in (0.0, 0.5, 1.0):
        z = z0 + (z1 - z0) * t
        cu = u + lean[0] * t + bow[0] * math.sin(math.pi * t)
        cw = w + lean[1] * t + bow[1] * math.sin(math.pi * t)
        s = 1.0 + (taper - 1.0) * t
        ang = twist * t
        ca, sa = math.cos(ang), math.sin(ang)
        corners = []
        for du, dw in ((a * s, -b * s), (a * s, b * s), (-a * s, b * s), (-a * s, -b * s)):
            corners.append((cu + ca * du - sa * dw, cw + sa * du + ca * dw))
        ring = np.array([wall.P(cu_, cw_, z) for cu_, cw_ in corners])
        if t == 1.0 and topz is not None:
            ring[:, 2] = [topz(p[0], p[1]) for p in ring]
        rings.append(ring)
    return loft(rings)


def stud_at(stud, z):
    """(centre u, centre w) of a stud at height z (its lean is a straight drift from foot to head)."""
    t = (z - stud['z0']) / (stud['z1'] - stud['z0'])
    return stud['u'] + stud['lean'][0] * t, stud['w'] + stud['lean'][1] * t
