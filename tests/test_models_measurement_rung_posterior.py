import pytest

from models.measurement import rung_transition_posterior


def test_posterior_matches_hand_computed_conjugate_update():
    # prior_p=0.2, pseudo_count=10 -> alpha0=2, beta0=8
    # 6 successes out of 20 trials -> alpha=8, beta=22, mean=8/30
    alpha, beta, mean = rung_transition_posterior(prior_p=0.2, pseudo_count=10, successes=6, trials=20)
    assert alpha == pytest.approx(8.0)
    assert beta == pytest.approx(22.0)
    assert mean == pytest.approx(8 / 30)


def test_posterior_with_zero_trials_returns_the_prior():
    alpha, beta, mean = rung_transition_posterior(prior_p=0.3, pseudo_count=10, successes=0, trials=0)
    assert mean == pytest.approx(0.3)


def test_posterior_moves_toward_observed_rate_with_more_data():
    # prior says 0.1, but observed rate is much higher (0.9) with a lot of data
    _, _, mean_small = rung_transition_posterior(prior_p=0.1, pseudo_count=10, successes=9, trials=10)
    _, _, mean_large = rung_transition_posterior(prior_p=0.1, pseudo_count=10, successes=900, trials=1000)
    assert mean_small > 0.1
    assert mean_large > mean_small  # more data pulls the posterior further from the prior, toward 0.9
    assert mean_large == pytest.approx(0.9, abs=0.01)


def test_posterior_rejects_invalid_counts():
    with pytest.raises(ValueError):
        rung_transition_posterior(prior_p=0.2, pseudo_count=10, successes=5, trials=3)
    with pytest.raises(ValueError):
        rung_transition_posterior(prior_p=0.2, pseudo_count=10, successes=-1, trials=3)
