from math import ceil
from math import log
from PIL import Image
from PIL import ImageDraw
from random import choice

BASES = '01'


class TrianglesEncoder:

    def __init__(self, image_size, n_triangles):
        self.image_size = image_size
        self.n_triangles = n_triangles
        self.frames_lengths = []
        width, height = image_size
        w_bit = ceil(log(width, 2))
        h_bit = ceil(log(height, 2))
        color_bit = ceil(log(256, 2))
        for i in range(n_triangles):
            for _ in range(3):
                self.frames_lengths.append(w_bit)
                self.frames_lengths.append(h_bit)
            self.frames_lengths.append(color_bit)
        self.w_bit = w_bit
        self.h_bit = h_bit
        self.color_bit = color_bit
        self.genome_length = n_triangles * ((w_bit + h_bit) * 3 +  color_bit)

    def generate(self):
        return ''.join([choice(BASES) for _ in range(self.genome_length)])

    def decode(self, dna):
        """
        Da una sequenza binaria produce `self.n_triangles` triangoli.
        """
        i = 0
        w_bit, h_bit = self.w_bit, self.h_bit
        color_bit = self.color_bit
        ret = []
        for i_triangle in range(self.n_triangles):
            # print('i_triangle =', i_triangle)
            triangle_points = []
            for i_point in range(3):
                # print('\ti_point =', i_point)
                x_tuplet = dna[i: i + w_bit]
                i += w_bit
                y_tuplet = dna[i: i + h_bit]
                i += h_bit
                triangle_points.append((int(x_tuplet, 2), int(y_tuplet, 2)))
                # print('\t\tx_tuplet =', x_tuplet)
                # print('\t\ty_tuplet =', y_tuplet)
                # print('\t\ttriangle_points =', triangle_points)
            color_tuplet = dna[i: i + color_bit]
            color = int(color_tuplet, 2)
            ret.append((tuple(triangle_points), color))
        return ret


def draw_triangles(im, triangles, save=False):
    drawer = ImageDraw.Draw(im)
    for points, color in triangles:
        drawer.polygon(points, outline=color)


def demo():
    image_size = 100, 100
    encoder = TrianglesEncoder(image_size, 3)
    dna = encoder.generate()
    print(dna, len(dna))
    triangles = encoder.decode(dna)
    print(triangles)
    im = Image.new('L', image_size, color=255)
    draw_triangles(im, triangles)
    im.save('drawed.png')


if __name__ == '__main__':
    demo()
