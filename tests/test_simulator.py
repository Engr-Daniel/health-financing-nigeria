import pytest

from healthfin.simulator import FX_DEFAULT, TARGETS, simulate


def test_abuja_headline():
    r = simulate(TARGETS[0])
    assert r.total_usd / 1e9 == pytest.approx(5.4, abs=0.2)
    assert r.total_ngn == pytest.approx(r.total_usd * FX_DEFAULT)
    assert 40 < r.oop_share1 < 50
    assert r.cata1 < r.cata0
    assert r.cata1_lo <= r.cata1 <= r.cata1_hi
    assert not r.at_floor and not r.effect_extrapolated
    assert 0 < r.deaths_averted_lo < r.deaths_averted_hi


@pytest.mark.parametrize("kind", TARGETS[1:3])
def test_large_targets_hit_floor(kind):
    r = simulate(kind)
    assert r.at_floor and r.effect_extrapolated
    assert r.oop_share1 == pytest.approx(15, abs=1e-6)


@pytest.mark.parametrize("theta", [0.2, 0.6, 0.9])
@pytest.mark.parametrize("floor", [0.05, 0.15, 0.3])
def test_oop_never_below_floor(theta, floor):
    for kind in TARGETS[:3]:
        r = simulate(kind, theta=theta, floor=floor)
        assert r.oop_share1 >= floor * 100 - 1e-6
        assert r.oop_pc1 >= 0
        assert r.gov_share1 + r.oop_share1 <= 100 + 1e-6


def test_more_substitution_lowers_oop():
    lo, hi = simulate(TARGETS[0], theta=0.3), simulate(TARGETS[0], theta=0.8)
    assert hi.oop_share1 < lo.oop_share1
    assert hi.total_usd == pytest.approx(lo.total_usd)  # cost depends on target, not theta


def test_custom_and_fx():
    r = simulate("Custom", custom=30.0, fx=2000)
    assert r.gov_pc1 == pytest.approx(30.0)
    assert r.total_ngn == pytest.approx(r.total_usd * 2000)
    below = simulate("Custom", custom=5.0)  # below today's spend: no cut is simulated
    assert below.delta_pc == 0 and below.total_usd == 0
