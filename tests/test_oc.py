from __future__ import annotations

import numpy as np
import pytest

from src.oc import gchsp_acceptance_probability


def test_gchsp_acceptance_probability_matches_research_formula():
    p = np.array([0.0, 0.05, 0.25, 1.0])
    g, r, i = 6, 2, 1
    expected = (1.0 - p) ** (g * r) + g * r * p * (1.0 - p) ** (g * r * (i + 1) - 1)

    actual = gchsp_acceptance_probability(p, g=g, r=r, i=i)

    np.testing.assert_allclose(actual, expected, rtol=0.0, atol=1e-15)
    assert actual[0] == pytest.approx(1.0)
    assert actual[-1] == pytest.approx(0.0)


def test_gchsp_acceptance_probability_is_bounded_and_nonincreasing():
    p = np.linspace(0.0, 1.0, 501)
    values = gchsp_acceptance_probability(p, g=3, r=4, i=3)

    assert np.all((values >= 0.0) & (values <= 1.0))
    assert np.all(np.diff(values) <= 1e-15)


@pytest.mark.parametrize("p", [[-0.01], [1.01], [np.nan]])
def test_gchsp_acceptance_probability_rejects_invalid_probabilities(p):
    with pytest.raises(ValueError):
        gchsp_acceptance_probability(p, g=1, r=2, i=1)
