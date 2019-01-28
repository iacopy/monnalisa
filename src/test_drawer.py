from drawer import draw_shapes, Shape


def test_draw_triangle():
    actual = draw_shapes((2, 2), dst_image_mode='L', draw_image_mode='L', shapes=[], shape=Shape.TRIANGLE, background_color='white')
    assert list(actual.getdata()) == [255, 255, 255, 255]
