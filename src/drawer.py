from math import ceil, log
from random import choice
from enum import Enum

from PIL import Image, ImageDraw
import svgwrite

BASES = '01'


class Shape(Enum):
    TRIANGLE = 't'
    ELLIPSE = 'e'
    QUAD = 'q'


POINTS_PER_SHAPE = {Shape.TRIANGLE: 3, Shape.ELLIPSE: 2, Shape.QUAD: 4}
CHANNELS_TO_IMAGE_MODE = {1: 'L', 2: 'LA', 3: 'RGB', 4: 'RGBA'}
IMAGE_MODES = list(CHANNELS_TO_IMAGE_MODE.values())


class ShapesEncoder:
    """
    Handle the generation of image based on binary strings.
    """
    def __init__(
            self,
            image_size=(100, 100),
            image_mode='RGB',
            draw_image_mode='RGBA',
            shape=Shape.TRIANGLE,
            n_shapes=32,
            color_bit_depth=8,
            symmetry='',
        ):
        print('ShapesEncoder init with image_mode={}'.format(image_mode))
        self.image_size = image_size
        assert image_mode in IMAGE_MODES, 'Invalid image mode: {}'.format(image_mode)
        assert draw_image_mode in IMAGE_MODES, 'Invalid draw_image_mode: {}'.format(draw_image_mode)
        self.image_mode = image_mode
        self.draw_image_mode = draw_image_mode
        self.color_channels = len(draw_image_mode)
        self.symmetry = symmetry
        self.bg_warned = False
        # TODO: refactor shape e n_shaoes in a single attribute
        self.shape = Shape(shape)
        self.n_shapes = n_shapes
        points_per_shape = POINTS_PER_SHAPE[self.shape]
        width, height = image_size
        size_bits = ceil(log(width, 2)), ceil(log(height, 2))
        color_bits = color_bit_depth * self.color_channels
        visible_bits = 1
        self.genome_size = color_bits + n_shapes * (
            visible_bits + color_bits + points_per_shape * sum(size_bits)
        )
        sb = sum(size_bits)
        print('genome_size = {color_bits} + {n_shapes} * ({visible_bits} + {color_bits} + {points_per_shape} * {sb})'.format(**locals()))

        self.bits = dict(
            channel=color_bits // self.color_channels,
            x=size_bits[0], y=size_bits[1],
            visible=visible_bits,
            color_depth=color_bit_depth,
        )
        print('self.bits =', self.bits)
        self.index = 0

    def _read(self, sequence, n_bits):
        """
        Read and decode a `sequence` chunk of `n_bits` in decimal.

        :rtype: int
        """
        chunk = sequence[self.index: self.index + n_bits]
        dec = int(chunk, 2)
        self.index += n_bits
        return dec  # TODO: optimize / remove intermediate variable

    def _read_points(self, sequence, n_points):
        """
        Read and decode `n_points` of 2D coordinates from `sequence`.
        """
        points = [(0, 0)] * n_points
        x_bits = self.bits['x']
        y_bits = self.bits['y']
        for i in range(n_points):
            x = self._read(sequence, x_bits)
            y = self._read(sequence, y_bits)
            points[i] = x, y
        return points

    def _read_color(self, sequence):
        """
        Read and decode a L, LA, RGB or RGBA color (based on self.color_channels).
        """
        return tuple(
            [self._read(sequence, self.bits['channel'])
                for _ in range(self.color_channels)]
        )

    def decode(self, sequence):
        """
        Translate a binary `sequence` into an high level drawing information.
        """
        self.index = 0
        shapes = []
        annotations = {}
        annotations['visibility'] = []  # list of visibility bases
        bg_color = self._read_color(sequence)
        visible_bits = self.bits['visible']
        points_per_shape = POINTS_PER_SHAPE[self.shape]
        while self.index < len(sequence):
            try:
                annotations['visibility'].append(self.index)
                visible = self._read(sequence, visible_bits)
                # read shape points
                points = self._read_points(sequence, points_per_shape)
                color = self._read_color(sequence)
            except ValueError as err:
                break
            else:
                if visible:
                    shapes.append((color, points))
        return {'background': bg_color, 'shapes': shapes,
                'annotations': annotations}

    def generate(self, set_visibility=None):
        """
        Generate a random binary string.

        :param set_visibility: set all shapes visible or not.
        """
        pre_seq = [choice(BASES) for _ in range(self.genome_size)]
        if set_visibility is not None:
            decoded = self.decode(''.join(pre_seq))
            for shape_visibility_pos in decoded['annotations']['visibility']:
                pre_seq[shape_visibility_pos] = str(int(set_visibility))
        return ''.join(pre_seq)

    def draw(self, sequence):
        """
        Convert `sequence` into a Pillow image (in memory).
        """
        decoded = self.decode(sequence)

        # FIXME: no worning but use less channels for the bg if needed
        if not self.bg_warned:
            bg_color = decoded['background'][: len(self.image_mode)]
            if bg_color != decoded['background']:
                print('WARNING: {} unused channel(s) for the background!'.format(
                    len(decoded['background']) - len(bg_color)
                ))
                self.bg_warned = True

        return draw_shapes(
            self.image_size, decoded['shapes'], self.shape,
            decoded['background'],
            dst_image_mode=self.image_mode,
            draw_image_mode=self.draw_image_mode,
            symmetry=self.symmetry,
        )

    def draw_as_svg(self, sequence, filename):
        if self.shape == 'e':
            return

        decoded = self.decode(sequence)
        width, height = self.image_size
        dwg = svgwrite.Drawing(filename=filename)
        dwg.viewbox(width=width, height=height)
        color = [v / 255 for v in decoded['background']]
        r, g, b, a = tuple_to_rgba(color)
        background = dwg.polygon(
            points=[(0, 0), (width, 0), (width, height), (0, height)],
            fill='rgb({}%, {}%, {}%)'.format(r * 100, g * 100, b * 100),
        )
        dwg.add(background)

        total_shapes = symmetrify_shapes(self.image_size, self.symmetry, decoded['shapes'])

        for color, points in total_shapes:
            color = [v / 255 for v in color]
            r, g, b, a = tuple_to_rgba(color)
            if self.shape is Shape.ELLIPSE:
                # ellipse not implemented
                continue
            else:
                shape = dwg.polygon(
                    points=points,
                    fill='rgb({}%, {}%, {}%)'.format(r * 100, g * 100, b * 100),
                    opacity=a)
            dwg.add(shape)
        dwg.save()


def tuple_to_rgba(color):
    color_length = len(color)
    if color_length == 4:
        r, g, b, a = color
    elif color_length == 3:
        r, g, b = color
        a = 1
    elif color_length == 2:
        r = g = b = color[0]
        a = color[1]
    elif color_length == 1:
        r = g = b = color[0]
        a = 1
    else:
        raise Exception('Unexpected color length: color = {}'.format(color))
    return r, g, b, a


def draw_shapes(
        image_size, shapes, shape,
        background_color='white',
        dst_image_mode='RGB',
        draw_image_mode='RGBA',
        symmetry='',
    ):
    """
    Create an RGB (by default) image and draw `shapes` on it
    in RGBA mode (with alpha).
    """
    # TODO: optimize by passing already created image
    # print('image_size =', image_size)
    # print('shapes =', shapes)
    # print('dst_image_mode =', dst_image_mode)
    # print('background_color =', background_color)
    # print('Creating {} image'.format(dst_image_mode))
    im = Image.new(dst_image_mode, image_size, color=background_color)
    # print('Drawing in {} mode'.format(draw_image_mode))
    drawer = ImageDraw.Draw(im, draw_image_mode)

    total_shapes = symmetrify_shapes(image_size, symmetry, shapes)

    for color, points in total_shapes:
        if shape is Shape.ELLIPSE:
            drawer.ellipse(points, color)
        else:
            drawer.polygon(points, color)
    return im


def symmetrify_shapes(image_size, symmetry, shapes):
    total = list(shapes)
    for element in symmetry:
        for color, points in shapes:
            total.append((color, get_symmetry(image_size, element, points)))
        shapes = list(total)
    total.sort()
    return total


def get_symmetry(image_size, symmetry_element, points):
    """
    Return symmetric points against given symmetry element.
    """
    width, height = image_size
    if symmetry_element == 'x':
        rv = [(width - x, y) for (x, y) in points]
    elif symmetry_element == 'y':
        rv = [(x, height - y) for (x, y) in points]
    elif symmetry_element == 'o':
        rv = [(width - x, height - y) for (x, y) in points]
    elif symmetry_element == '.':
        return points
    else:
        raise Exception('Invalid symmetry_element value: "{}"'.format(symmetry_element))
    return rv



def demo():
    image_size = 100, 100
    encoder = ShapesEncoder(image_size, 4, Shape.TRIANGLE)
    dna = encoder.generate()
    print(dna, len(dna))
    im = encoder.draw(dna)
    im.save('drawed.png')


if __name__ == '__main__':
    demo()
