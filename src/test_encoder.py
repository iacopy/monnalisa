from drawer import ShapesEncoder, Shape
import pytest


@pytest.mark.parametrize('case', [
    {'size': (1, 1), 'n': 1, 'shape': 'e', 'expected': 32 + 1 * (32 + (0 + 0) + (0 + 0) * 2 + 1)},
    {'size': (2, 2), 'n': 1, 'shape': 'e', 'expected': 32 + 1 * (32 + (1 + 1) + (1 + 1) * 2 + 1)},
    {'size': (2, 2), 'n': 1, 'shape': 't', 'expected': 32 + 1 * (32 + (1 + 1) + (1 + 1) * 3 + 1)},
    {'size': (4, 2), 'n': 2, 'shape': 't', 'expected': 32 + 2 * (32 + (2 + 1) + (2 + 1) * 3 + 1)},
])
def test_rgba_genome_size(case):
    encoder = ShapesEncoder(
        image_size=case['size'],
        image_mode='RGBA',
        shape=case['shape'],
        n_shapes=case['n'],
    )
    assert encoder.genome_size == case['expected']


def test_decode_rgba():
    encoder = ShapesEncoder(
        image_size=(2, 2),
        image_mode='RGBA',
        shape='e',
        n_shapes=1,
    )
    seq = ''.join([
        '0' * 32,  # background color
        '1',       # first ellipse visibility
        '00',      # posizione di partenza
        '01',      # punto 1
        '10',      # punto 2
        '1' * 32,  # ellipse color
    ])
    actual = encoder.decode(seq)
    assert actual == {
        'background': (0, 0, 0, 0),
        'shapes': [
            (
                [(0, 1), (1, 0)],
                (255, 255, 255, 255),
            ),
        ],
        'annotations': {'visibility': [32]},
    }


@pytest.mark.parametrize('im_size,im_mode,n_shapes,shape,expected', [
    [(2, 3), 'L', 2, 'q', 8 + 2 * (1 + (1 + 2) + 4 * (1 + 2) + 8)],
    [(2, 3), 'LA', 2, 'q', 16 + 2 * (1 + (1 + 2) + 4 * (1 + 2) + 16)],
])
def test_encode_grayscale_genome_size(im_size, im_mode, n_shapes, shape, expected):
    encoder = ShapesEncoder(image_size=im_size, image_mode=im_mode, draw_image_mode=im_mode, n_shapes=n_shapes, shape=shape)
    assert encoder.genome_size == expected, \
        'Expected genome size: {}. Actual: {}'.format(expected, encoder.genome_size)


@pytest.mark.parametrize('case', [
    {
        'genome': '0000000010000011011111111',
        'background': (0, ),
        'shapes': [([(0, 0), (0, 1), (1, 0)], (255,))],
    },
    {
        'genome': '0000000110000011011111110',
        'background': (1, ),
        'shapes': [([(0, 0), (0, 1), (1, 0)], (254,))],
    },
    # visibility 0 at pos 8
    {
        'genome': '0000000101100011011111110',
        'background': (1, ),
        'shapes': [],
    },
    # All ones
    {
        'genome': '1111111110011111111111111',
        'background': (255, ),
        'shapes': [([(1, 1), (1, 1), (1, 1)], (255,))],
    },
    # Extra length
    {
        'genome': '11111111100111111111111110000',
        'background': (255, ),
        'shapes': [([(1, 1), (1, 1), (1, 1)], (255,))],
    },
])
def test_grayscale(case):
    encoder = ShapesEncoder(image_size=(2, 2), image_mode='L', draw_image_mode='L', n_shapes=1, shape=Shape.TRIANGLE)
    dec = encoder.decode(case['genome'])
    assert dec['background'] == case['background']
    assert dec['shapes'] == case['shapes']
