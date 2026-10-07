from agents.m6.channels import build_channels_from_pack
from models.backtest import backtest_recommended_vs_current
from models.optimiser import optimise_mix
from packs.loader import load_pack


def test_recommended_mix_beats_naive_equal_split_on_held_out_periods():
    """Gate 3: 'optimiser beats historical mix in backtest'. 'Historical mix'
    here is a naive equal spend split across channels — the obvious baseline
    a brand falls back to without an optimiser — replayed against the real
    channels' own response curves over 12 held-out synthetic months."""
    pack = load_pack("india")
    channels = build_channels_from_pack(pack, rep_count=50)
    # varied, not uniform, so reallocation actually has somewhere better to go
    fit_scores = {c.channel_ref: 0.5 + 0.05 * i for i, c in enumerate(channels)}
    budget = 50_000.0
    hcp_count = 500

    n = len(channels)
    current_spend = {c.channel_ref: budget / n for c in channels}

    recommended = optimise_mix(channels, fit_scores, budget, hcp_count, freq_caps=pack.frequency_caps)
    recommended_spend = {r.channel_id: r.spend for r in recommended}

    result = backtest_recommended_vs_current(channels, fit_scores, current_spend, recommended_spend, periods=12)

    assert result.recommended_total_response >= result.current_total_response
    assert result.uplift > 0


def test_recommended_mix_matches_current_when_current_is_already_optimal():
    """Sanity check on the harness itself: if 'current' already IS the
    optimiser's own recommendation, uplift should be ~0, not spuriously
    positive or negative."""
    pack = load_pack("india")
    channels = build_channels_from_pack(pack, rep_count=50)
    fit_scores = {c.channel_ref: 1.0 for c in channels}
    budget = 50_000.0
    hcp_count = 500

    recommended = optimise_mix(channels, fit_scores, budget, hcp_count, freq_caps=pack.frequency_caps)
    recommended_spend = {r.channel_id: r.spend for r in recommended}

    result = backtest_recommended_vs_current(channels, fit_scores, recommended_spend, recommended_spend, periods=12)

    assert result.uplift == 0.0
