from math import ceil
from math import log
from PIL import Image
from PIL import ImageDraw
from random import choice


BASES = '01'


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
        self.visible_bits = 1
        n_polygons = int(n_total_sides / max_sides)
        self.genome_size = self.color_bits * self.colors_channels + \
            n_total_sides * (self.width_bits + self.height_bits) + \
            n_polygons * (self.visible_bits + self.sides_bits + self.color_bits * self.colors_channels)
        self.index = 0
        self.polygons = []

    def _read(self, sequence, n_bits, info=''):
        """
        :param info: annotate the sequence when decoding.
        """
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

        self.annotations[info].append((self.index, self.index + n_bits))

    def decode(self, sequence):
        self.index = 0
        polygons = []
        annotations = {}
        annotations['visibility'] = []  # list of visibility bases
        #print('Decoding sequence', sequence, len(sequence))
        bg_color = self._read_color(sequence)
        while self.index < len(sequence):
            try:
                annotations['visibility'].append(self.index)
                visible = self._read(sequence, self.visible_bits)
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
                if visible:
                    polygons.append((points, color))
        return {'background': bg_color, 'polygons': polygons,
                'annotations': annotations}

    def generate(self, set_visibility=None):
        """
        :param set_visibility: set all polygons visible or not.
        """
        pre_seq = [choice(BASES) for _ in range(self.genome_size)]
        if set_visibility is not None:
            # print('change visibility to', str(int(set_visibility)))
            decoded = self.decode(''.join(pre_seq))
            for polygon_visibility_pos in decoded['annotations']['visibility']:
                # print('{} = {} => {}'.format(
                #     polygon_visibility_pos, pre_seq[polygon_visibility_pos], set_visibility))
                pre_seq[polygon_visibility_pos] = str(int(set_visibility))
        return ''.join(pre_seq)

    def draw(self, sequence, target_image_mode='RGB'):
        decoded = self.decode(sequence)
        return draw_polygons(
            self.image_size, decoded['polygons'], decoded['background'],
            target_image_mode=target_image_mode
        )


def draw_polygons(image_size, polygons, background_color='white',
                  target_image_mode='RGB'):
    """
    Create an RGB (by default) image and draw `polygons` on it
    in RGBA mode (with alpha).
    """
    im = Image.new(target_image_mode, image_size, color=background_color)
    drawer = ImageDraw.Draw(im, 'RGBA')
    for points, color in polygons:
        drawer.polygon(points, color)
    return im


def demo():
    image_size = 100, 100
    encoder = PolygonsEncoder(image_size, 4)
    dna = encoder.generate()
    print(dna, len(dna))
    im = encoder.draw(dna)
    im.save('drawed.png')


if __name__ == '__main__':
    demo()
