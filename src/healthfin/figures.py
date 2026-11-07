"""README / brief figures.  Run: python src/healthfin/figures.py"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healthfin.financing import OOP_SAFE, SOURCES, cata_curve, mix, ssa_latest  # noqa: E402
from healthfin.model import load  # noqa: E402
from healthfin.paths import FIGURES  # noqa: E402
from healthfin.simulator import TARGETS, simulate  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#ecebe7"
COL = {"gov_share": "#2a78d6", "ext_share": "#1baf7a", "oop_share": "#eb6834", "other_pvt_share": "#b9b7b0"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.edgecolor": "#d6d4ce", "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True, "figure.dpi": 150})
NOTE = ("Daniel Oyewale · Petgrave.io · Data: WHO Global Health Expenditure Database via World Bank HNP Statistics "
        "(CC BY 4.0)")


def _save(fig, name, title, sub, foot_y=-0.04):
    fig.subplots_adjust(top=0.78)
    fig.text(0.01, 0.97, title, ha="left", va="top", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.01, 0.885, sub, ha="left", va="top", fontsize=9.5, color=INK2)
    fig.text(0.01, foot_y, NOTE, ha="left", va="top", fontsize=7.5, color="#8a8984")
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def financing_mix():
    m = mix()
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.stackplot(m.year, *[m[c] for c, _ in SOURCES], colors=[COL[c] for c, _ in SOURCES],
                 labels=[lab for _, lab in SOURCES], edgecolor="white", linewidth=0.8)
    last = m.iloc[-1]
    y = 0
    for c, lab in SOURCES:
        v = last[c]
        if v > 4:
            ax.text(m.year.max() + 0.4, y + v / 2, f"{lab.split(' (')[0]} {v:.0f}%", va="center", fontsize=9.5, color=INK)
        y += v
    ax.set_xlim(m.year.min(), m.year.max())
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(100))
    ax.set_ylabel("Share of current health expenditure")
    ax.legend(frameon=False, ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=9)
    fig.subplots_adjust(right=0.8)
    _save(fig, "01_financing_mix.png", "Nigerian households pay for most of their own healthcare",
          f"Sources of current health expenditure, {m.year.min()}–{m.year.max()}; each year sums to 100%")


def peers():
    d = ssa_latest(2023)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    other = d[d.iso3 != "NGA"]
    ax.scatter(other.gov_pc_usd, other.oop_share, s=34, color="#9ec5f4", edgecolor="white", linewidth=0.8, zorder=2)
    ng = d[d.iso3 == "NGA"].iloc[0]
    ax.scatter([ng.gov_pc_usd], [ng.oop_share], s=110, color="#eb6834", edgecolor="white", linewidth=1.5, zorder=3)
    ax.annotate(f"Nigeria\n{ng.oop_share:.0f}% OOP · ${ng.gov_pc_usd:.0f} gov/person", (ng.gov_pc_usd, ng.oop_share),
                xytext=(12, -4), textcoords="offset points", fontsize=9.5, color=INK, va="top")
    for _, r in other.nlargest(3, "gov_pc_usd").iterrows():
        ax.annotate(r["name"], (r.gov_pc_usd, r.oop_share), xytext=(5, 4), textcoords="offset points", fontsize=8, color=INK2)
    ax.axhspan(15, OOP_SAFE, color="#1baf7a", alpha=0.12, lw=0)
    ax.text(ax.get_xlim()[0] if False else 1.05, 17.5, "15–20%: financial hardship becomes negligible", fontsize=8.5,
            color="#0f6b4b", va="center")
    ax.set_xscale("log")
    ax.set_xticks([1, 3, 10, 30, 100, 300])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel("Government health spending per person, US$ (log scale)")
    ax.set_ylabel("Out-of-pocket, % of health spending")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(100))
    _save(fig, "02_ssa_peers.png", "Nigeria has the highest out-of-pocket share in sub-Saharan Africa",
          f"{len(d)} sub-Saharan countries, 2023 or latest. Each dot is one country.", foot_y=-0.05)


def protection_curve():
    fit, d = cata_curve()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    other = d[d.iso3 != "NGA"]
    ax.scatter(other.oop_share, other.cata10, s=26, color="#9ec5f4", edgecolor="white", linewidth=0.6)
    x = np.linspace(0, 85, 100)
    ax.plot(x, np.exp(fit["a"] + fit["b"] * x), color="#2a78d6", lw=2)
    ng = d[d.iso3 == "NGA"]
    if len(ng):
        r = ng.iloc[0]
        ax.scatter([r.oop_share], [r.cata10], s=100, color="#eb6834", edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(f"Nigeria {int(r.year)}: {r.cata10:.1f}% of people", (r.oop_share, r.cata10), xytext=(-10, 12),
                    textcoords="offset points", ha="right", fontsize=9.5, color=INK)
    ax.set_xlabel("Out-of-pocket, % of health spending")
    ax.set_ylabel("People spending >10% of budget on health")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(100))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(100))
    _save(fig, "03_catastrophic_vs_oop.png", "The more households pay directly, the more face catastrophic costs",
          f"{fit['n']} countries, latest survey since 2010 (SDG 3.8.2). Line: log-linear fit, R² = {fit['r2']:.2f}.")


def coefficients():
    m = load()
    specs = [("main", "Within-country (2-way FE)"), ("long_difference", "Long-run change (2000–04 → 2018–22)"),
             ("cross_section", "Between countries (2018–22)")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, (var, title, scale) in zip(axes, [("ln_gov_pc", "Government health spending ×2", np.log(2)),
                                              ("oop10", "Out-of-pocket share +10 points", 1)]):
        ys, labels = [], []
        for i, (k, lab) in enumerate(specs):
            c = m[k]["u5mr"]["coef"][var]
            est, lo, hi = [(np.exp(v * scale) - 1) * 100 for v in (c["b"], c["lo"], c["hi"])]
            col = "#eb6834" if c["p"] < 0.05 else "#7e8aa3"
            ax.plot([lo, hi], [i, i], color=col, lw=2.5)
            ax.scatter([est], [i], color=col, s=55, zorder=3, edgecolor="white")
            ax.text(hi + 0.8, i, f"{est:+.1f}%" + (" *" if c["p"] < 0.05 else ""), va="center", fontsize=9.5, color=INK)
            ys.append(i)
            labels.append(lab)
        ax.axvline(0, color=INK2, lw=1, ls="--")
        lo_, hi_ = ax.get_xlim()
        ax.set_xlim(lo_, hi_ + (hi_ - lo_) * 0.3)
        ax.set_title(title, fontsize=10.5, color=INK, loc="left")
        ax.set_yticks(ys, labels)
        ax.set_xlabel("Change in under-5 mortality (%)")
        ax.grid(axis="y", visible=False)
        ax.invert_yaxis()
    fig.subplots_adjust(wspace=0.08, left=0.26)
    _save(fig, "04_what_drives_child_mortality.png", "Lower out-of-pocket reliance, not spending alone, goes with fewer child deaths",
          "Sub-Saharan Africa, controlling for GDP per capita. Bars: 95% CI; orange * = significant at 5%. Associations, not causal effects.",
          foot_y=-0.08)


def scenarios():
    rs = [simulate(k) for k in TARGETS[:3]]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    names = ["Today (2023)"] + ["Abuja 15%", "5% of GDP", "US$86/person"]
    oop = [rs[0].oop_share0] + [r.oop_share1 for r in rs]
    cost = [0] + [r.total_usd / 1e9 for r in rs]
    ax = axes[0]
    bars = ax.barh(names[::-1], oop[::-1], color=["#9ec5f4"] * 3 + ["#eb6834"], height=0.6)
    for b_, v in zip(bars, oop[::-1]):
        ax.text(v + 1, b_.get_y() + b_.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9.5, color=INK)
    ax.axvspan(15, 20, color="#1baf7a", alpha=0.15, lw=0)
    ax.set_xlim(0, 85)
    ax.set_title("Out-of-pocket share of health spending", fontsize=10.5, loc="left", color=INK)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(100))
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    bars = ax.barh(names[::-1][:-1], cost[::-1][:-1], color="#2a78d6", height=0.6)
    for b_, v, r in zip(bars, cost[::-1][:-1], rs[::-1]):
        ax.text(v + 0.4, b_.get_y() + b_.get_height() / 2, f"${v:.1f}bn · {r.pct_gdp:.1f}% GDP", va="center", fontsize=9.5,
                color=INK)
    ax.set_xlim(0, max(cost) * 1.55)
    ax.set_title("Extra government spending a year", fontsize=10.5, loc="left", color=INK)
    ax.grid(axis="y", visible=False)
    fig.subplots_adjust(wspace=0.45)
    _save(fig, "05_scenarios.png", "Reaching the Abuja target would cut the out-of-pocket share from 72% to ~44%",
          "Per year, 2023 US$. 60% of new public money assumed to replace household payments; out-of-pocket floor 15%.",
          foot_y=-0.06)


def main():
    financing_mix()
    peers()
    protection_curve()
    coefficients()
    scenarios()
    print("figures written to", FIGURES)


if __name__ == "__main__":
    main()
