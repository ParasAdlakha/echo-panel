import numpy as np

from echo import metrics as M


def _panel(rho, k=4000, seed=0):
    rng = np.random.default_rng(seed)
    common = rng.normal(size=(k, 1))
    own = rng.normal(size=(k, 5))
    return np.sqrt(rho) * common + np.sqrt(1 - rho) * own


def test_independent_advisors_count_as_five():
    E = _panel(0.0)
    assert abs(M.n_eff(M.mean_pairwise_corr(E)) - 5) < 0.3
    assert abs(M.n_eff_variance(E) - 5) < 0.4


def test_identical_advisors_count_as_one():
    E = np.repeat(np.random.default_rng(1).normal(size=(500, 1)), 5, axis=1) + 1e-9 * np.random.default_rng(2).normal(size=(500, 5))
    assert M.n_eff(M.mean_pairwise_corr(E)) < 1.01


def test_half_correlated():
    E = _panel(0.5)
    assert abs(M.n_eff(M.mean_pairwise_corr(E)) - 5 / 3) < 0.15


def test_naive_pool_is_more_extreme_than_mean():
    P = np.full((3, 5), 0.7)
    assert np.all(M.naive_pool(P, 0.5) > 0.95)
    assert np.allclose(M.neff_pool(P, 0.5, 1.0), 0.7, atol=1e-6)


def test_unanimity():
    P = np.array([[0.9] * 5, [0.1] * 5, [0.9, 0.1, 0.9, 0.9, 0.9]])
    u = M.unanimity(P, np.array([1, 1, 0]))
    assert u["k"] == 2 and u["acc"] == 0.5


def test_conditional_corr_independent_given_truth():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 2, 3000)
    L = (2 * y - 1)[:, None] * 0.8 + rng.normal(size=(3000, 5))  # informative, conditionally independent
    P = 1 / (1 + np.exp(-L))
    assert abs(M.conditional_corr(P, y)) < 0.05
    assert M.mean_pairwise_corr(P - y[:, None]) > 0.5  # raw error correlation is misleadingly high
