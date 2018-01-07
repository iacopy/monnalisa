import pytest

from utils import AccumulativeMean


@pytest.mark.parametrize('values,expected_means', [
    [[0, 0, 0], [0.0, 0.0, 0.0]],
    [[7, 7, 7], [7.0, 7.0, 7.0]],
    [[1, 2, 3], [1.0, 1.5, 2.0]],
])
def test_accumulative_mean__no_init_args(values, expected_means):
    am = AccumulativeMean()
    for value, expected in zip(values, expected_means):
        assert am.update(value) == expected

    assert am.get_count() == len(values)


@pytest.mark.parametrize('init_args,new_value,expected', [
    [(10, 1), 20, 15.0],
])
def test_accumulative_mean__init_args(init_args, new_value, expected):
    am = AccumulativeMean(*init_args)
    am += new_value
    assert am.get_current() == expected
