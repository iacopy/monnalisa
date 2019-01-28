from math import ceil, log
from random import choice

from drawer import Shape, IMAGE_MODES, POINTS_PER_SHAPE, draw_shapes

BASES = '01'


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
        # TODO: refactor shape e n_shapes in a single attribute
        self.shape = Shape(shape)
        self.n_shapes = n_shapes
        points_per_shape = POINTS_PER_SHAPE[self.shape]
        width, height = image_size
        size_bits = ceil(log(width, 2)), ceil(log(height, 2))
        color_bits = color_bit_depth * self.color_channels
        visible_bits = 1
        self.genome_size = color_bits + n_shapes * (
            visible_bits + color_bits + sum(size_bits) + points_per_shape * sum(size_bits)
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
                position = self._read_points(sequence, 1)[0]
                # read shape points
                points = self._read_points(sequence, points_per_shape)
                for i, point in enumerate(points):
                    points[i] = position[0] + point[0], position[1] + point[1]
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


def demo():
    """
    Create a random generated image.
    """
    image_size = 100, 100
    encoder = ShapesEncoder(
        image_size, image_mode='RGB', draw_image_mode='RGBA',
        shape=Shape.TRIANGLE, n_shapes=64, color_bit_depth=8, symmetry='x',
    )
    dna = encoder.generate()
    print(dna, len(dna))
    image = encoder.draw(dna)
    image.save('drawed.png')
    print('Open drawer.png to see the random generated picture.')


if __name__ == '__main__':
    demo()
