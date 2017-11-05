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


class ImageEvaluator:
    def __init__(self, target_image):
        im = Image.open(target_image).convert('L')
        dirpath, filename = os.path.split(target_image)
        name, ext = os.path.splitext(filename)
        self.target_dst_dir = os.path.join(dirpath, name)
        try:
            os.makedirs(self.target_dst_dir)
        except FileExistsError:
            print('Directory already exists:', self.target_dst_dir)
        im.save(os.path.join(self.target_dst_dir, name + '_L' + ext))
        self.target_size = im.size
        self.target_data = np.array(im.getdata()) / 255
        self.n_data = len(self.target_data)

    def evaluate(self, image):
        """Mean Squared Error
        """
        return (
            ((self.target_data - np.array(image.getdata()) / 255) ** 2) / self.n_data
        ).sum()


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
