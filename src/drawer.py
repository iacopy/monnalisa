from math import ceil
from math import log
from PIL import Image
from PIL import ImageDraw
from random import choice
import numpy as np
import os


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
        self.genome_size = n_triangles * ((w_bit + h_bit) * 3 + color_bit)

    def generate(self):
        return ''.join([choice(BASES) for _ in range(self.genome_size)])

    def decode(self, dna):
        """
        Da una sequenza binaria produce poligoni.
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
            i += color_bit
            ret.append((tuple(triangle_points), color))
        return ret


def draw_triangles(image_size, triangles, background_color=255, save=False):
    """Create an image and draw triangles on it.
    """
    im = Image.new('L', image_size, color=background_color)
    drawer = ImageDraw.Draw(im)
    for points, color in triangles:
        drawer.polygon(points, outline=color)
    return im


class PolygonsEncoder:
    def __init__(self, image_size, n_total_sides, min_sides=3, max_sides=4):
        width, height = image_size
        self.width_bits = ceil(log(width, 2))
        self.height_bits = ceil(log(height, 2))
        self.image_size = image_size
        sides_span = max_sides - min_sides + 1
        self.sides = tuple(range(min_sides, max_sides + 1))
        self.sides_bits = ceil(log(sides_span, 2))
        self.color_bits = ceil(log(256, 2))
        self.colors_channels = 4
        n_polygons = int(n_total_sides / max_sides)
        self.genome_size = self.color_bits * self.colors_channels + \
            n_total_sides * (self.width_bits + self.height_bits) + \
            n_polygons * (self.sides_bits + self.color_bits * self.colors_channels)
        self.index = 0

    def _read(self, sequence, n_bits):
        chunk = sequence[self.index: self.index + n_bits]
        dec = int(chunk, 2)
        #print('chunk = {}, dec = {}'.format(chunk, dec), end=' ')
        self.index += n_bits
        return dec

    def _read_points(self, sequence, n_points):
        points = [(0, 0)] * n_points
        for i in range(n_points):
            x = self._read(sequence, self.width_bits)
            y = self._read(sequence, self.height_bits)
            points[i] = x, y
        return points

    def _read_color(self, sequence):
        """Read and decode an RGB or RGBA color (based on self.color_channels).
        """
        return tuple(
            [self._read(sequence, self.color_bits)
                for _ in range(self.colors_channels)]
        )

    def decode(self, sequence):
        self.index = 0
        polygons = []
        #print('Decoding sequence', sequence, len(sequence))
        n_chunks = 0
        bg_color = self._read_color(sequence)
        while self.index < len(sequence):
            #print(self.index, n_chunks)
            n_chunks += 1
            try:
                n_sides = self.sides[self._read(sequence, self.sides_bits)]
                #print('n_sides =', n_sides)
                # read polygon
                points = self._read_points(sequence, n_sides)
                #print('points:', points)
                color = self._read_color(sequence)
                #print('color:', color)
            except ValueError as err:
                #print(err)
                break
            else:
                polygons.append((points, color))
        return {'background': bg_color, 'polygons': polygons}

    def generate(self):
        return ''.join([choice(BASES) for _ in range(self.genome_size)])


def draw_polygons(image_size, polygons, background_color='white', image_mode='RGB'):
    im = Image.new(image_mode, image_size, color=background_color)
    drawer = ImageDraw.Draw(im, 'RGBA')
    for points, color in polygons:
        drawer.polygon(points, color)
    return im


class ImageEvaluator:
    def __init__(self, target_image, mode='RGB'):
        im = Image.open(target_image).convert(mode)
        dirpath, filename = os.path.split(target_image)
        name, ext = os.path.splitext(filename)
        self.target_dst_dir = os.path.join(dirpath, name)
        try:
            os.makedirs(self.target_dst_dir)
        except FileExistsError:
            print('Directory already exists:', self.target_dst_dir)
        im.save(os.path.join(self.target_dst_dir, name + '_' + mode + ext))
        self.target_image = im
        self.target_size = im.size
        self.target_arr = np.asarray(im.getdata())
        self.n_data = len(self.target_arr)
        # Create here, one time, the numpy array, whose the creation is the bottleneck
        self.candidate_arr = np.zeros(self.target_arr.shape, np.uint8)

    def evaluate(self, image):
        """Mean Squared Error
        """
        self.candidate_arr[:] = image.getdata()
        return ((self.target_arr - self.candidate_arr) ** 2).sum()


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
