from enum import Enum

import svgwrite
from PIL import Image, ImageDraw


class Shape(Enum):
    CIRCLE = 'c'
    ELLIPSE = 'e'
    QUAD = 'q'
    RECT = 'r'
    TRIANGLE = 't'


POINTS_PER_SHAPE = {
    Shape.CIRCLE: 1,
    Shape.ELLIPSE: 2,
    Shape.QUAD: 4,
    Shape.RECT: 2,
    Shape.TRIANGLE: 3,
}
CHANNELS_TO_IMAGE_MODE = {1: 'L', 2: 'LA', 3: 'RGB', 4: 'RGBA'}
IMAGE_MODES = list(CHANNELS_TO_IMAGE_MODE.values())


def draw_as_svg(filename,
                image_size, shapes, shape,
                dst_image_mode='RGB',
                draw_image_mode='RGBA',
                symmetry='',
                ):
    if shape is Shape.ELLIPSE:
        return

    width, height = image_size
    dwg = svgwrite.Drawing(filename=filename)
    dwg.viewbox(width=width, height=height)
    total_shapes = symmetrify_shapes(image_size, symmetry, shapes)

    for color, points in total_shapes:
        color = [v / 255 for v in color]
        r, g, b, a = tuple_to_rgba(color)
        if shape is Shape.ELLIPSE:
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
    # print('Creating {} image'.format(dst_image_mode))
    im = Image.new(dst_image_mode, image_size, color='white')
    # print('Drawing in {} mode'.format(draw_image_mode))
    drawer = ImageDraw.Draw(im, draw_image_mode)

    total_shapes = symmetrify_shapes(image_size, symmetry, shapes)

    for color, points in total_shapes:
        if shape is Shape.ELLIPSE:
            drawer.ellipse(points, color)
        elif shape is Shape.CIRCLE:
            drawer.ellipse((points[0], (points[0][0] + 10, points[0][1] + 10)), color)
        elif shape is Shape.RECT:
            drawer.rectangle(points, color)
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
