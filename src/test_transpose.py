import pytest
from hypothesis import strategies as st
from hypothesis import assume, given

from transpose import transpose


def test_reverse_whole_sequence():
    """
    Caso di trasposizione con inversione di tutta la sequenza.

    Test a case of transposition in which the sequence results totally reversed.
    """
    seq = list('012345')
    transpose(seq, 0, 5, 6, replicative=False, inverted=True)
    assert seq == list('543210')


def test_reverse_subseq_inplace():
    """
    Testa una trasposizione di sequenza con inversione, sul posto.

    Test an inverted transposition in place.
    """
    seq = list('012345')
    transpose(seq, 2, 4, 4, replicative=False, inverted=True)
    # '23' -> '32'
    assert seq == list('013245')


def test_rotate():
    """Rotazione della sequenza tramite trasposizione non replicativa"""
    seq = list('012345')
    transpose(seq, 0, 2, 6, replicative=False)
    # rotate left by 2
    assert seq == list('234501')


@given(
    start=st.integers(min_value=0, max_value=10),
    end=st.integers(min_value=0, max_value=10),
    dst=st.integers(min_value=0, max_value=10),
    inverted=st.booleans(),
)
def test_transpose_outside_for_length_and_set(start, end, dst, inverted):
    """
    Testa che una sottosequenza spostata "fuori" [#]_ da se stessa non riservi sorprese [#]_.

    .. [#] Con "fuori" si intende che il punto di destinazione è esterno alla sottosequenza sorgente.
    .. [#] Nessun accorciamento strano o eliminazione di caratteri.
    """
    assume((start <= end <= dst) or (dst <= start <= end))
    seq = list('0123456789')
    assert len(seq) == len(set(seq)) == 10

    transpose(seq, start, end, dst, replicative=False, inverted=inverted)
    assert len(seq) == len(set(seq)) == 10


@given(
    start=st.integers(min_value=0, max_value=10),
    end=st.integers(min_value=0, max_value=10),
    dst=st.integers(min_value=0, max_value=10),
    inverted=st.booleans(),
)
def test_transpose_outside_replicative_for_length_and_set(start, end, dst, inverted):
    """
    Testa che una sottosequenza copincollata "fuori" [#]_ da se stessa non riservi sorprese [#]_.

    .. [#] Con "fuori" si intende che il punto di destinazione è esterno alla sottosequenza sorgente.
    .. [#] Nessun accorciamento strano o eliminazione di caratteri.
    """
    assume((start <= end <= dst) or (dst <= start <= end))
    seq = list('0123456789')
    assert len(seq) == len(set(seq)) == 10
    src = ''.join(seq[start: end])
    crs = ''.join(reversed(seq[start: end]))

    transpose(seq, start, end, dst, replicative=True, inverted=inverted)
    assert len(seq) == 10 + (end - start)
    assert len(set(seq)) == 10
    if src:
        stringed = ''.join(seq)
        if inverted and len(src) > 1:
            assert stringed.count(src) == 1
            assert stringed.count(crs) == 1
        else:
            assert stringed.count(src) == 2


# ------------------
# strange edge cases
# ------------------


@pytest.mark.xfail
def test_transpose_inside_for_set():
    """
    Warning: spostare una sottosequenza dentro se stessa causa perdita qualitativa di caratteri.

    In altre parole, la lunghezza della sequenza viene conservata, ma la dimensione
    dell'insieme dei caratteri che la compongono no. Uno scompare e un altro si duplica.

    Sarebbe bello non succedesse, ma per ora accetto la mancanza di
    questo caso particolare, dato che comunque provoca una mutazione e la
    lunghezza rimane invariata.
    """
    seq = list('012345')
    assert len(seq) == 6
    assert len(set(seq)) == 6

    transpose(seq, 1, 4, 2)
    assert len(seq) == 6
    assert len(set(seq)) == 6
    assert seq == list('045123')
