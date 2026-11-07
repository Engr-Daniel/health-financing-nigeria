"""Who pays for health: financing mix, peer comparison, benchmarks and financial protection."""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healthfin.paths import PANEL  # noqa: E402

SSA = "Sub-Saharan Africa"
SOURCES = [("gov_share", "Government"), ("ext_share", "External donors"), ("oop_share", "Out-of-pocket"),
           ("other_pvt_share", "Other private (insurance, NGOs, employers)")]
# Benchmarks (sources in data/reference/assumptions.csv)
OOP_SAFE = 20          # financial hardship becomes negligible when OOP is 15-20% of CHE (WHO WHR 2010; World Bank)
ABUJA = 15             # % of government budget on health (Abuja Declaration 2001)
GOV_GDP = 5            # government health spending, % GDP (McIntyre, Meheus & Røttingen 2017)
GOV_PC_2015USD = 86    # government health spending per capita, 2015 US$ (HLTF / McIntyre et al. 2017)
CPI_2015_TO_2023 = 304.702 / 237.017   # US CPI-U annual averages (BLS)


@lru_cache(maxsize=1)
def panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def latest(df: pd.DataFrame, col: str, since: int = 2015) -> pd.DataFrame:
    """Most recent non-missing value per country (from `since`)."""
    d = df[(df.year >= since) & df[col].notna()].sort_values("year")
    return d.groupby("iso3").tail(1)


def mix(iso3: str = "NGA") -> pd.DataFrame:
    """Financing mix by year; the four sources sum to 100% of current health expenditure."""
    d = panel()
    d = d[(d.iso3 == iso3) & d.oop_share.notna()][["year"] + [c for c, _ in SOURCES]].copy()
    tot = d[[c for c, _ in SOURCES]].sum(axis=1)
    for c, _ in SOURCES:                       # rescale tiny rounding residuals so stacks sum to exactly 100
        d[c] = d[c] / tot * 100
    return d.reset_index(drop=True)


def ssa_latest(year: int = 2023) -> pd.DataFrame:
    """Sub-Saharan peers in a given year (or their latest within 3 years)."""
    d = panel()
    d = d[(d.region == SSA) & d.year.between(year - 3, year) & d.oop_share.notna()].sort_values("year")
    return d.groupby("iso3").tail(1).reset_index(drop=True)


def nigeria_rank(col: str, year: int = 2023, higher_is_worse: bool = True) -> tuple[int, int]:
    s = ssa_latest(year).dropna(subset=[col]).sort_values(col, ascending=not higher_is_worse).reset_index(drop=True)
    return int(s.index[s.iso3 == "NGA"][0]) + 1, len(s)


def benchmarks(year: int = 2023) -> dict:
    """Nigeria versus the financing benchmarks, latest year."""
    n = panel()[(panel().iso3 == "NGA") & (panel().year == year)].iloc[0]
    gov_pc_target = GOV_PC_2015USD * CPI_2015_TO_2023
    return {
        "year": year, "oop_share": n.oop_share, "oop_target": OOP_SAFE,
        "gov_budget_share": n.gov_budget_share, "abuja": ABUJA,
        "gov_gdp": n.gov_gdp, "gov_gdp_target": GOV_GDP,
        "gov_pc_usd": n.gov_pc_usd, "gov_pc_target_usd": gov_pc_target,
        "che_pc_usd": n.che_pc_usd, "population": n.population, "u5mr": n.u5mr, "mmr": n.mmr, "births": n.births,
        "gdp_pc_usd": n.che_pc_usd / (n.che_gdp / 100),
        "gge_pc_usd": n.gov_pc_usd / (n.gov_budget_share / 100),   # general government expenditure per capita
    }


def protection(iso3: str = "NGA") -> pd.DataFrame:
    d = panel()
    return d[(d.iso3 == iso3) & d.cata10.notna()][["year", "cata10", "cata25", "cata10_n", "impov215", "population"]]


def cata_curve(since: int = 2010):
    """Cross-country relationship: catastrophic spending (>10% of budget) vs OOP share of health spending.

    Fits log(cata10) = a + b * oop_share on each country's latest survey since `since`, matched to that year's OOP
    share. Returns (fit dict, data). Used to translate a lower OOP share into an indicative catastrophic-spending rate.
    """
    d = panel()
    d = d[(d.year >= since) & d.cata10.notna() & d.oop_share.notna() & (d.cata10 > 0)].sort_values("year")
    d = d.groupby("iso3").tail(1)
    X = np.column_stack([np.ones(len(d)), d.oop_share.values])
    y = np.log(d.cata10.values)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = resid @ resid / (len(y) - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    r2 = 1 - resid.var() / y.var()
    return {"a": beta[0], "b": beta[1], "cov": cov.tolist(), "r2": r2, "n": len(d)}, d
