"""
Simulates DNA transposable elements, which cause mutations.

Supports also replicative and inverted transposition, combined or not.
"""


def transpose(seq, start, end, dst, replicative=False, inverted=False):
    """
    Move/copy a sublist along list, *in place*.

    If `replicative` is True, copy the sublist to `dst`, else move it.
    If `inverted` is True, the transposed element will be inserted reversed.

    Simulates DNA transposable elements.
    Works with mutable sequences like list and array.array.

    NB: Works as expected when `start <= end` and
    `dst` is *outside* the sublist (i.e. `dst <= start` or `dst >= end`).
    Otherwise, same chars could be duplicated and others removed.

    :param seq: source sequence
    :param start: transposing start point
    :param end: transposing end point
    :param dst: transposing destination point
    :rtype: None

    >>> seq = [0, 1, 2, 3, 4, 5]
    >>> transpose(seq, 1, 3, 5)
    >>> seq
    [0, 3, 4, 1, 2, 5]
    >>> transpose(seq, 3, 5, 1)
    >>> seq
    [0, 1, 2, 3, 4, 5]

    >>> seq = [0, 1, 2, 3, 4, 5]
    >>> transpose(seq, 3, 5, 1, inverted=True)
    >>> seq
    [0, 4, 3, 1, 2, 5]

    >>> seq = list('ABCDEFGH')
    >>> transpose(seq, 2, 4, 4, replicative=True)
    >>> seq
    ['A', 'B', 'C', 'D', 'C', 'D', 'E', 'F', 'G', 'H']
    """
    if inverted:
        for e in seq[start: end]:
            seq.insert(dst, e)
    else:
        for e in reversed(seq[start: end]):
            seq.insert(dst, e)

    if not replicative:
        el_len = end - start
        cut_start = start
        if dst < start:
            cut_start = start + el_len
        del seq[cut_start: cut_start + el_len]
