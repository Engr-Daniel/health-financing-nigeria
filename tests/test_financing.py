import numpy as np
import pytest

from healthfin.financing import SOURCES, benchmarks, cata_curve, mix, nigeria_rank, panel, ssa_latest


def test_panel_shape():
    p = panel()
    assert p.year.between(2000, 2024).all()
    assert p.region.notna().all()  # aggregates removed
    assert (p.iso3 == "NGA").any()
    assert p[p.region == "Sub-Saharan Africa"].iso3.nunique() >= 45


def test_mix_sums_to_100():
    m = mix()
    total = m[[c for c, _ in SOURCES]].sum(axis=1)
    assert np.allclose(total, 100, atol=1e-6)
    assert (m[[c for c, _ in SOURCES]] >= 0).all().all()


def test_nigeria_benchmarks():
    b = benchmarks()
    assert b["year"] == 2023
    assert 65 < b["oop_share"] < 80
    assert 3 < b["gov_budget_share"] < 6
    assert b["gov_pc_usd"] < 20
    assert b["gov_pc_target_usd"] == pytest.approx(86 * 304.702 / 237.017, rel=1e-6)


def test_nigeria_highest_oop_in_ssa():
    rank, n = nigeria_rank("oop_share")
    assert rank == 1 and n >= 45
    assert len(ssa_latest(2023)) == n


def test_cata_curve_positive_gradient():
    fit, data = cata_curve()
    assert fit["b"] > 0 and fit["n"] >= 100
    assert data.cata10.gt(0).all()
