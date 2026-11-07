"""Panel models: is government health spending (and lower OOP reliance) associated with better outcomes in SSA?

Two-way fixed effects (country + year), standard errors clustered by country. Government health spending is
lagged one year. These are associations, not causal effects: fixed effects remove stable country traits and common
shocks, but not time-varying confounders or reverse causality.
Run:  python src/healthfin/model.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healthfin.financing import SSA, panel  # noqa: E402
from healthfin.paths import MODELS  # noqa: E402

OUTCOMES = {"u5mr": ("log", "Under-5 mortality"), "mmr": ("log", "Maternal mortality"),
            "uhc_index": ("level", "UHC service coverage index")}


def design(exclude: tuple = (), lag: int = 1, start: int = 2000) -> pd.DataFrame:
    d = panel()
    d = d[(d.region == SSA) & ~d.iso3.isin(exclude) & (d.year >= start)].sort_values(["iso3", "year"]).copy()
    g = d.groupby("iso3")
    d["ln_gov_pc"] = np.log(g.gov_pc_ppp.shift(lag)) if lag else np.log(d.gov_pc_ppp)
    d["oop10"] = (g.oop_share.shift(lag) if lag else d.oop_share) / 10   # per 10 percentage points
    d["ln_gdp"] = np.log(d.gdp_pc_ppp)
    d["ln_u5mr"], d["ln_mmr"] = np.log(d.u5mr), np.log(d.mmr)
    return d


def fit(outcome: str, exclude: tuple = (), lag: int = 1, with_oop: bool = True) -> dict:
    d = design(exclude, lag)
    y = f"ln_{outcome}" if OUTCOMES[outcome][0] == "log" else outcome
    xs = ["ln_gov_pc"] + (["oop10"] if with_oop else []) + ["ln_gdp"]
    m = d.dropna(subset=[y] + xs).set_index(["iso3", "year"])
    res = PanelOLS(m[y], m[xs], entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
    ci = res.conf_int()
    return {
        "outcome": outcome, "label": OUTCOMES[outcome][1], "form": OUTCOMES[outcome][0], "lag": lag,
        "excluded": list(exclude), "n_obs": int(res.nobs), "n_countries": int(m.index.get_level_values(0).nunique()),
        "years": [int(m.index.get_level_values(1).min()), int(m.index.get_level_values(1).max())],
        "r2_within": float(res.rsquared_within),
        "coef": {k: {"b": float(res.params[k]), "se": float(res.std_errors[k]), "p": float(res.pvalues[k]),
                     "lo": float(ci.loc[k, "lower"]), "hi": float(ci.loc[k, "upper"])} for k in xs},
    }


def long_difference(y0=(2000, 2004), y1=(2018, 2022)) -> dict:
    """Change between period averages (about 18 years apart): removes country fixed traits, robust to slow trends."""
    import statsmodels.api as sm
    d = panel()
    d = d[d.region == SSA]
    cols = ["gov_pc_ppp", "gdp_pc_ppp", "u5mr", "mmr", "oop_share"]
    a = d[d.year.between(*y0)].groupby("iso3")[cols].mean()
    b = d[d.year.between(*y1)].groupby("iso3")[cols].mean()
    ld = pd.DataFrame({"ln_gov_pc": np.log(b.gov_pc_ppp / a.gov_pc_ppp), "oop10": (b.oop_share - a.oop_share) / 10,
                       "ln_gdp": np.log(b.gdp_pc_ppp / a.gdp_pc_ppp), "u5mr": np.log(b.u5mr / a.u5mr),
                       "mmr": np.log(b.mmr / a.mmr)}).dropna()
    out = {}
    for o in ("u5mr", "mmr"):
        r = sm.OLS(ld[o], sm.add_constant(ld[["ln_gov_pc", "oop10", "ln_gdp"]])).fit(cov_type="HC1")
        ci = r.conf_int()
        out[o] = {"outcome": o, "label": OUTCOMES[o][1], "form": "log", "n_obs": int(r.nobs), "n_countries": int(r.nobs),
                  "periods": [list(y0), list(y1)],
                  "coef": {k: {"b": float(r.params[k]), "se": float(r.bse[k]), "p": float(r.pvalues[k]),
                               "lo": float(ci.loc[k, 0]), "hi": float(ci.loc[k, 1])} for k in ("ln_gov_pc", "oop10", "ln_gdp")}}
    return out


def cross_section(years=(2018, 2022)) -> dict:
    """Between-country association (period averages). Most exposed to confounding; shown for comparison only."""
    import statsmodels.api as sm
    d = panel()
    x = (d[(d.region == SSA) & d.year.between(*years)].groupby("iso3")[["gov_pc_ppp", "gdp_pc_ppp", "u5mr", "mmr", "oop_share"]]
         .mean().dropna())
    X = sm.add_constant(pd.DataFrame({"ln_gov_pc": np.log(x.gov_pc_ppp), "oop10": x.oop_share / 10, "ln_gdp": np.log(x.gdp_pc_ppp)}))
    out = {}
    for o in ("u5mr", "mmr"):
        r = sm.OLS(np.log(x[o]), X).fit(cov_type="HC1")
        ci = r.conf_int()
        out[o] = {"outcome": o, "label": OUTCOMES[o][1], "form": "log", "n_obs": int(r.nobs), "n_countries": int(r.nobs),
                  "coef": {k: {"b": float(r.params[k]), "se": float(r.bse[k]), "p": float(r.pvalues[k]),
                               "lo": float(ci.loc[k, 0]), "hi": float(ci.loc[k, 1])} for k in ("ln_gov_pc", "oop10", "ln_gdp")}}
    return out


def run_all() -> dict:
    out = {"main": {o: fit(o) for o in OUTCOMES},
           "robust_no_lag": {o: fit(o, lag=0) for o in OUTCOMES},
           "robust_excl_nigeria": {o: fit(o, exclude=("NGA",)) for o in OUTCOMES},
           "robust_gov_only": {o: fit(o, with_oop=False) for o in OUTCOMES},
           "long_difference": long_difference(), "cross_section": cross_section()}
    MODELS.write_text(json.dumps(out, indent=1))
    return out


def load() -> dict:
    return json.loads(MODELS.read_text()) if MODELS.exists() else run_all()


def table(models: dict) -> pd.DataFrame:
    """Readable coefficient table for the main specification."""
    names = {"ln_gov_pc": "Gov. health spending per capita (log, t−1)", "oop10": "OOP share (+10 pp, t−1)",
             "ln_gdp": "GDP per capita PPP (log)"}
    rows = []
    for o, r in models.items():
        for k, c in r["coef"].items():
            eff = (f"{(np.exp(c['b'] * np.log(2)) - 1):+.1%} per doubling" if k == "ln_gov_pc" and r["form"] == "log"
                   else f"{c['b'] * np.log(2):+.2f} pts per doubling" if k == "ln_gov_pc"
                   else f"{(np.exp(c['b']) - 1):+.1%}" if r["form"] == "log" else f"{c['b']:+.2f} pts")
            rows.append({"Outcome": r["label"], "Variable": names[k], "Coefficient": c["b"], "95% CI":
                         f"[{c['lo']:.3f}, {c['hi']:.3f}]", "p": c["p"], "Interpretation": eff,
                         "Obs.": r["n_obs"], "Countries": r["n_countries"]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    res = run_all()
    print(table(res["main"]).round(3).to_string(index=False))
    for k in ("long_difference", "cross_section"):
        print(k, {o: {v: (round(c["b"], 3), round(c["p"], 3)) for v, c in r["coef"].items()} for o, r in res[k].items()})
    for k in ("robust_no_lag", "robust_excl_nigeria", "robust_gov_only"):
        print(k, {o: round(r["coef"]["ln_gov_pc"]["b"], 3) for o, r in res[k].items()})
