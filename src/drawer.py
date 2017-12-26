from math import ceil, log
from random import choice

from PIL import Image, ImageDraw
import svgwrite

BASES = '01'


class ShapesEncoder:
    def __init__(self, image_size, n_shapes, shape):
        self.shape = shape
        if shape == 'e':
            self.points_per_shape = 2
        elif shape == 't':
            self.points_per_shape = 3
        else:
            self.points_per_shape = 4
        n_total_points = n_shapes * self.points_per_shape
        width, height = image_size
        self.width_bits = ceil(log(width, 2))
        self.height_bits = ceil(log(height, 2))
        self.image_size = image_size
        self.color_bits = ceil(log(256, 2))
        self.colors_channels = 4
        self.visible_bits = 1
        self.genome_size = self.color_bits * self.colors_channels + \
            n_total_points * (self.width_bits + self.height_bits) + \
            n_shapes * (self.visible_bits + self.color_bits * self.colors_channels)
        self.index = 0

    def _read(self, sequence, n_bits, info=''):
        """
        :param info: annotate the sequence when decoding.
        """
        chunk = sequence[self.index: self.index + n_bits]
        dec = int(chunk, 2)
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
        shapes = []
        annotations = {}
        annotations['visibility'] = []  # list of visibility bases
        bg_color = self._read_color(sequence)
        while self.index < len(sequence):
            try:
                annotations['visibility'].append(self.index)
                visible = self._read(sequence, self.visible_bits)
                # read shape points
                points = self._read_points(sequence, self.points_per_shape)
                color = self._read_color(sequence)
            except ValueError as err:
                break
            else:
                if visible:
                    shapes.append((points, color))
        return {'background': bg_color, 'shapes': shapes,
                'annotations': annotations}

    def generate(self, set_visibility=None):
        """
        :param set_visibility: set all shapes visible or not.
        """
        pre_seq = [choice(BASES) for _ in range(self.genome_size)]
        if set_visibility is not None:
            decoded = self.decode(''.join(pre_seq))
            for shape_visibility_pos in decoded['annotations']['visibility']:
                pre_seq[shape_visibility_pos] = str(int(set_visibility))
        return ''.join(pre_seq)

    def draw(self, sequence, target_image_mode='RGB'):
        decoded = self.decode(sequence)
        return draw_shapes(
            self.image_size, decoded['shapes'], self.shape,
            decoded['background'],
            target_image_mode=target_image_mode
        )

    def draw_as_svg(self, sequence, filename):
        if self.shape == 'e':
            return

        decoded = self.decode(sequence)
        width, height = self.image_size
        dwg = svgwrite.Drawing(filename=filename)
        dwg.viewbox(width=width, height=height)
        r, g, b, a = [v / 255 for v in decoded['background']]
        background = dwg.polygon(
            points=[(0, 0), (width, 0), (width, height), (0, height)],
            fill='rgb({}%, {}%, {}%)'.format(r * 100, g * 100, b * 100),
        )
        dwg.add(background)
        for points, color in decoded['shapes']:
            r, g, b, a = [v / 255 for v in color]
            if self.shape == 'e':
                # ellipse not implemented
                continue
            else:
                shape = dwg.polygon(
                    points=points,
                    fill='rgb({}%, {}%, {}%)'.format(r * 100, g * 100, b * 100),
                    opacity=a)
            dwg.add(shape)
        dwg.save()


def draw_shapes(
        image_size, shapes, shape, background_color='white', target_image_mode='RGB'):
    """
    Create an RGB (by default) image and draw `shapes` on it
    in RGBA mode (with alpha).
    """
    im = Image.new(target_image_mode, image_size, color=background_color)
    drawer = ImageDraw.Draw(im, 'RGBA')
    for points, color in shapes:
        if shape == 'e':
            drawer.ellipse(points, color)
        else:
            drawer.polygon(points, color)
    return im


def demo():
    image_size = 100, 100
    encoder = ShapesEncoder(image_size, 4, 't')
    dna = encoder.generate()
    print(dna, len(dna))
    im = encoder.draw(dna)
    im.save('drawed.png')


if __name__ == '__main__':
    demo()
