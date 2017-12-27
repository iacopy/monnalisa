from drawer import ShapesEncoder
import pytest


@pytest.mark.parametrize('case', [
    {'size': (1, 1), 'n': 1, 'shape': 'e', 'expected': 32 + 1 * (32 + (0 + 0) * 2 + 1)},
    {'size': (2, 2), 'n': 1, 'shape': 'e', 'expected': 32 + 1 * (32 + (1 + 1) * 2 + 1)},
    {'size': (2, 2), 'n': 1, 'shape': 't', 'expected': 32 + 1 * (32 + (1 + 1) * 3 + 1)},
    {'size': (4, 2), 'n': 2, 'shape': 't', 'expected': 32 + 2 * (32 + (2 + 1) * 3 + 1)},
])
def test_genome_lenght(case):
    encoder = ShapesEncoder(
        image_size=case['size'],
        color_channels=4,
        shape=case['shape'],
        n_shapes=case['n'],
    )
    assert encoder.genome_size == case['expected']


def test_decode():
    encoder = ShapesEncoder(
        image_size=(2, 2),
        color_channels=4,
        shape='e',
        n_shapes=1,
    )
    seq = ''.join([
        '0' * 32,  # background color
        '1',       # first ellipse visibility
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
