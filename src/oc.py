"""Validated Group Chain Sampling Plan operating-characteristic calculations."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def gchsp_acceptance_probability(
    p: ArrayLike,
    *,
    g: int,
    r: int,
    i: int,
) -> NDArray[np.float64]:
    r"""Return the GChSP acceptance probability over failure probabilities ``p``.

    The implemented research definition is

    .. math::

       L_g(p)=(1-p)^{gr}+gr\,p(1-p)^{gr(i+1)-1}.

    Parameters are validated rather than clipped so invalid inputs cannot be
    silently converted into apparently valid probabilities.
    """

    if isinstance(g, bool) or not isinstance(g, (int, np.integer)) or g < 1:
        raise ValueError("g must be a positive integer.")
    if isinstance(r, bool) or not isinstance(r, (int, np.integer)) or r < 1:
        raise ValueError("r must be a positive integer.")
    if isinstance(i, bool) or not isinstance(i, (int, np.integer)) or i < 0:
        raise ValueError("i must be a nonnegative integer.")

    probability = np.asarray(p, dtype=np.float64)
    if not np.all(np.isfinite(probability)):
        raise ValueError("p must contain only finite values.")
    if np.any((probability < 0.0) | (probability > 1.0)):
        raise ValueError("p must lie within [0, 1].")

    sample_size = int(g) * int(r)
    survival_probability = 1.0 - probability
    return np.power(survival_probability, sample_size) + sample_size * probability * np.power(
        survival_probability,
        sample_size * (int(i) + 1) - 1,
    )
