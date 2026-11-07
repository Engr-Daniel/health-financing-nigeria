"""Funding-gap simulator: what would it cost Nigeria to reach a public-financing benchmark, and what might change?

Baseline = Nigeria 2023 (WHO GHED via World Bank). Mechanics, per person per year (2023 US$):
  new government spending  G1 = target;  ΔG = G1 − G0
  out-of-pocket            OOP1 = max(floor·CHE1, OOP0 − θ·ΔG)    θ = share of new public money that replaces household
                           payments; floor = residual OOP share (copayments, uncovered care), default 15%
  total health spending    CHE1 = CHE0 + ΔG − (OOP0 − OOP1)
Effects (indicative, with ranges):
  * catastrophic spending  scaled from Nigeria's last survey using the cross-country OOP-share gradient
  * under-5 mortality      scaled with the OOP-share coefficient, low = panel FE, high = long-difference model
"""
from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healthfin.financing import ABUJA, GOV_GDP, benchmarks, cata_curve, panel, protection  # noqa: E402
from healthfin.model import load  # noqa: E402

FX_DEFAULT = 1500        # ₦ per US$: 2025 federal budget assumption
FED_BUDGET_2025 = 54.99e12           # approved 2025 federal budget, ₦
FED_HEALTH_2025 = 2.38e12            # approved 2025 federal health allocation, ₦ (4.33%)
STATES_HEALTH_2025 = 2.36e12         # 36 states' combined 2025 health budgets, ₦ (Nigeria Governors' Forum)
BHCPF_2025 = 282.65e9                # BHCPF in the 2025 budget proposal (≈1% of the Consolidated Revenue Fund)


@dataclass
class Result:
    target: str
    theta: float
    floor: float
    at_floor: bool
    beyond_data: bool
    effect_extrapolated: bool
    gov_pc0: float
    gov_pc1: float
    delta_pc: float
    total_usd: float
    total_ngn: float
    pct_gdp: float
    oop_pc0: float
    oop_pc1: float
    che_pc0: float
    che_pc1: float
    oop_share0: float
    oop_share1: float
    gov_share1: float
    cata0: float
    cata1: float
    cata1_lo: float
    cata1_hi: float
    people_protected: float
    u5_change_lo: float
    u5_change_hi: float
    deaths_averted_lo: float
    deaths_averted_hi: float
    multiple_of_fed_health: float
    cata_year: int


def target_gov_pc(kind: str, custom: float | None = None) -> float:
    b = benchmarks()
    return {"Abuja: 15% of government budget": ABUJA / 100 * b["gge_pc_usd"],
            "5% of GDP": GOV_GDP / 100 * b["gdp_pc_usd"],
            "US$86 per person (2015 $)": b["gov_pc_target_usd"],
            "Custom": custom if custom is not None else b["gov_pc_usd"]}[kind]


TARGETS = ["Abuja: 15% of government budget", "5% of GDP", "US$86 per person (2015 $)", "Custom"]


def simulate(kind: str = TARGETS[0], theta: float = 0.6, fx: float = FX_DEFAULT, custom: float | None = None,
             floor: float = 0.15) -> Result:
    b = benchmarks()
    p = panel()
    n = p[(p.iso3 == "NGA") & (p.year == b["year"])].iloc[0]
    g0, che0 = n.gov_pc_usd, n.che_pc_usd
    oop0 = n.oop_share / 100 * che0
    g1 = max(target_gov_pc(kind, custom), g0)
    dg = g1 - g0
    oop1 = oop0 - theta * dg
    che1 = che0 + dg - (oop0 - oop1)
    at_floor = oop1 < floor * che1
    if at_floor:                                   # households keep paying a residual share (copayments, uncovered care)
        oop1 = floor * (che0 + dg - oop0) / (1 - floor)
        che1 = che0 + dg - (oop0 - oop1)
    s0, s1 = 100 * oop0 / che0, 100 * oop1 / che1
    # catastrophic spending (>10% of household budget): Nigeria's latest survey, shifted along the cross-country gradient
    fit, _ = cata_curve()
    pr = protection()
    last = pr.iloc[-1]
    oop_at_survey = p[(p.iso3 == "NGA") & (p.year == last.year)].oop_share.iloc[0]
    bse = np.sqrt(fit["cov"][1][1])
    cata = lambda bb: float(last.cata10 * np.exp(bb * (s1 - oop_at_survey)))  # noqa: E731
    cata0 = float(last.cata10 * np.exp(fit["b"] * (s0 - oop_at_survey)))
    c1, c_lo, c_hi = cata(fit["b"]), cata(fit["b"] + 1.96 * bse), cata(max(0.0, fit["b"] - 1.96 * bse))
    # under-5 mortality via the OOP-share coefficient (per 10 pp): low = panel FE, high = long-difference
    m = load()
    b_lo = max(0.0, m["main"]["u5mr"]["coef"]["oop10"]["b"])
    b_hi = max(0.0, m["long_difference"]["u5mr"]["coef"]["oop10"]["b"])
    ch = lambda bb: float(np.exp(bb * (s1 - s0) / 10) - 1)  # noqa: E731
    u_lo, u_hi = ch(b_lo), ch(b_hi)
    deaths = lambda c: float(-c * b["u5mr"] / 1000 * b["births"])  # noqa: E731
    total = dg * b["population"]
    ssa = p[(p.region == "Sub-Saharan Africa") & p.oop_share.notna()]
    beyond = bool(s1 < ssa.oop_share.quantile(0.05))
    extrap = bool(abs(s1 - s0) > max_observed_oop_change())
    return Result(
        target=kind, theta=theta, floor=floor, at_floor=bool(at_floor), beyond_data=beyond,
        effect_extrapolated=extrap, gov_pc0=g0, gov_pc1=g1, delta_pc=dg, total_usd=total, total_ngn=total * fx,
        pct_gdp=100 * dg / b["gdp_pc_usd"], oop_pc0=oop0, oop_pc1=oop1, che_pc0=che0, che_pc1=che1,
        oop_share0=s0, oop_share1=s1, gov_share1=100 * g1 / che1, cata0=cata0, cata1=c1, cata1_lo=min(c_lo, c_hi),
        cata1_hi=max(c_lo, c_hi), people_protected=(cata0 - c1) / 100 * b["population"],
        u5_change_lo=u_lo, u5_change_hi=u_hi, deaths_averted_lo=deaths(u_lo), deaths_averted_hi=deaths(u_hi),
        multiple_of_fed_health=total * fx / FED_HEALTH_2025, cata_year=int(last.year))


def all_targets(theta: float = 0.6, fx: float = FX_DEFAULT) -> list[dict]:
    return [asdict(simulate(k, theta, fx)) for k in TARGETS[:3]]


def max_observed_oop_change() -> float:
    """Largest absolute change in OOP share (pp) between 2000-04 and 2018-22 among SSA countries."""
    p = panel()
    d = p[p.region == "Sub-Saharan Africa"]
    a = d[d.year.between(2000, 2004)].groupby("iso3").oop_share.mean()
    b = d[d.year.between(2018, 2022)].groupby("iso3").oop_share.mean()
    return float((b - a).abs().max())


def ssa_oop_p05() -> float:
    p = panel()
    return float(p[(p.region == "Sub-Saharan Africa") & p.oop_share.notna()].oop_share.quantile(0.05))


if __name__ == "__main__":
    for r in all_targets():
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
