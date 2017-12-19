import pytest
from monnalisa import islands_crossover_offsprings_tournament


@pytest.mark.parametrize('islands,ev_offsprings,expected', [
    [[10, 40], [20, 25], {0: 1}],
    [[5, 10, 55], [2, 4], {0: 0, 1: 1}],
    [[10, 20, 30], [100, 13, 7], {2: 0, 1: 1}],
    [[10, 10], [10, 10], {}],
    [[7, 11], [7, 11], {0: 1}],
])
def test_things(islands, ev_offsprings, expected):
    rv = islands_crossover_offsprings_tournament(islands, ev_offsprings)
    assert rv == expected
