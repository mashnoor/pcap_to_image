#!/usr/bin/env python
import os.path, string, sys
from drawing import scurve
from drawing.scurve import utils
from PIL import Image, ImageDraw


class _Color:
    def __init__(self, data, block):
        self.data, self.block = data, block
        s = list(set(data))
        s.sort()
        self.symbol_map = {v : i for (i, v) in enumerate(s)}

    def __len__(self):
        return len(self.data)

    def point(self, x):
        if self.block and (self.block[0]<=x<self.block[1]):
            return self.block[2]
        else:
            return self.getPoint(x)


class ColorGradient(_Color):
    def getPoint(self, x):
        c = self.data[x]/255.0
        return [
            int(255*c),
            int(255*c),
            int(255*c)
        ]


class ColorHilbert(_Color):
    def __init__(self, data, block):
        _Color.__init__(self, data, block)
        self.csource = scurve.fromSize("hilbert", 3, 256**3)
        self.step = len(self.csource)/float(len(self.symbol_map))

    def getPoint(self, x):
        c = self.symbol_map[self.data[x]]
        return self.csource.point(int(c*self.step))


class ColorClass(_Color):
    def getPoint(self, x):
        # c = ord(self.data[x])
        c = self.data[x]
        if c == 0:
            return [0, 0, 0]
        elif c == 255:
            return [255, 255, 255]
        elif chr(c) in string.printable:
            return [55, 126, 184]
        return [228, 26, 28]


class ColorEntropy(_Color):
    def getPoint(self, x):
        e = utils.entropy(self.data, 32, x, len(self.symbol_map))
        def curve(v):
            f = (4*v - 4*v**2)**4
            f = max(f, 0)
            return f
        r = curve(e-0.5) if e > 0.5 else 0
        b = e**2
        return [
            int(255*r),
            0,
            int(255*b)
        ]


def drawmap_unrolled(map, size, csource, name):
    map = scurve.fromSize(map, 2, size**2)
    c = Image.new("RGB", (size, size*4))
    cd = ImageDraw.Draw(c)
    step = len(csource)/float(len(map)*4)

    sofar = 0
    for quad in range(4):
        for i, p in enumerate(map):
            off = (i + (quad * size**2))
            color = csource.point(
                        int(off * step)
                    )
            x, y = tuple(p)
            cd.point(
                (x, y + (size * quad)),
                fill=tuple(color)
            )
            sofar += 1
    c.save(name)


def drawmap_square(map, size, csource, name):
   
    map = scurve.fromSize(map, 2, size**2)
    c = Image.new("RGB", map.dimensions())
    cd = ImageDraw.Draw(c)
    step = len(csource)/float(len(map))
    for i, p in enumerate(map):
        color = csource.point(int(i*step))
        cd.point(tuple(p), fill=tuple(color))
    c.save(name)




def draw_bin(infile, outfile=None, color="class", map="hilbert", suffix="", size=256, type="unrolled"):
    with open(infile, 'rb') as f:
        d = f.read()
    if outfile:
        dst = outfile
    else:
        base = os.path.basename(infile)
        if "." in base:
            base, _ = base.rsplit(".", 1)
        dst = base + suffix + ".png"

    if os.path.exists(dst) and not outfile:
        print("Refusing to over-write '%s'. Specify explicitly if you really want to do this."%dst, file=sys.stderr)
        return

 
    if color == "class":
        csource = ColorClass(d, None)
    elif color == "hilbert":
        csource = ColorHilbert(d, None)
    elif color == "gradient":
        csource = ColorGradient(d, None)
    else:
        csource = ColorEntropy(d, None)

   

    if type == "unrolled":
        drawmap_unrolled(map, size, csource, dst)
    elif type == "square":
        drawmap_square(map, size, csource, dst)


# binvis(infile='01_03_03.pcap', outfile='01_03_03.pcap.png', map='hilbert', color='hilbert', type='square')