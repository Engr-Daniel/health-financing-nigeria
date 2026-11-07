"""Who pays for healthcare in Nigeria?  Run: streamlit run app/streamlit_app.py  (UI only - logic in src/healthfin)"""
import html
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from healthfin.financing import (ABUJA, GOV_GDP, OOP_SAFE, SOURCES, benchmarks, cata_curve, mix,  # noqa: E402
                                 nigeria_rank, protection, ssa_latest)
from healthfin.model import load, table  # noqa: E402
from healthfin.simulator import (BHCPF_2025, FED_BUDGET_2025, FED_HEALTH_2025, FX_DEFAULT, STATES_HEALTH_2025,  # noqa: E402
                                 TARGETS, max_observed_oop_change, simulate)

INK, INK2, INK3, BORDER, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e7e5e0", "#ecebe7"
BLUE, ORANGE, AQUA, GREY, NAVY = "#2a78d6", "#eb6834", "#1baf7a", "#b9b7b0", "#0d366b"
COL = {"gov_share": BLUE, "ext_share": AQUA, "oop_share": ORANGE, "other_pvt_share": GREY}
REPO = "https://github.com/Engr-Daniel/health-financing-nigeria"

st.set_page_config(page_title="Who pays for healthcare in Nigeria?", page_icon="🩺", layout="wide",
                   initial_sidebar_state="auto")
st.markdown(f"""<style>
  .block-container {{padding-top:1.4rem; padding-bottom:3rem; max-width:1380px;}}
  [data-testid="stSidebar"] {{border-right:1px solid {BORDER};}}
  .hero {{background:linear-gradient(120deg,#5a1e0e 0%,#8c3418 45%,{NAVY} 100%); color:#fff; border-radius:18px;
          padding:26px 30px 22px; margin-bottom:18px;}}
  .hero .eyebrow {{font-size:.74rem; letter-spacing:.12em; text-transform:uppercase; opacity:.85; font-weight:600;}}
  .hero h1 {{color:#fff; font-size:2.0rem; line-height:1.2; margin:6px 0 8px; padding:0;}}
  .hero p {{color:rgba(255,255,255,.88); margin:0; max-width:900px; line-height:1.5;}}
  .hero .meta {{display:flex; flex-wrap:wrap; gap:8px; margin-top:16px;}}
  .chip {{font-size:.76rem; padding:4px 11px; border-radius:999px; background:rgba(255,255,255,.12);
          border:1px solid rgba(255,255,255,.25); color:#fff;}}
  .kpis {{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:6px;}}
  .kpi {{background:#fff; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px 14px; min-height:124px;
         box-shadow:0 1px 2px rgba(16,24,40,.04);}}
  .kpi .l {{font-size:.7rem; color:{INK2}; text-transform:uppercase; letter-spacing:.07em; font-weight:700;}}
  .kpi .v {{font-size:1.8rem; font-weight:700; color:{INK}; margin-top:8px; line-height:1.15; font-variant-numeric:tabular-nums;}}
  .kpi .v span {{font-size:.9rem; font-weight:500; color:{INK2};}}
  .kpi .s {{font-size:.8rem; color:{INK2}; margin-top:6px; line-height:1.35;}}
  .headline {{font-size:1.08rem; line-height:1.55; color:{INK}; background:#fff; border:1px solid {BORDER};
             border-radius:12px; padding:14px 18px; margin:4px 0 16px;}}
  .card {{background:#fff; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px; height:100%;}}
  .card h4 {{margin:0 0 10px; padding:0; font-size:.98rem;}}
  .muted {{color:{INK2}; font-size:.86rem; line-height:1.5;}}
  .msg {{display:flex; gap:12px; margin-bottom:12px;}}
  .msg .n {{flex:0 0 26px; height:26px; border-radius:50%; background:{NAVY}; color:#fff; font-weight:700; font-size:.8rem;
           display:flex; align-items:center; justify-content:center;}}
  .msg .t {{font-weight:700; font-size:.92rem;}} .msg .b {{font-size:.86rem; color:{INK2}; line-height:1.45;}}
  .sec {{font-size:1.18rem; font-weight:700; color:{INK}; margin:22px 0 2px;}}
  .sec-sub {{font-size:.88rem; color:{INK2}; margin:0 0 12px;}}
  .warn {{font-size:.86rem; color:#7a4a00; background:#fbf3e3; border:1px solid #efd9a6; border-radius:10px; padding:10px 14px; margin:6px 0;}}
  .foot {{border-top:1px solid {BORDER}; margin-top:34px; padding-top:14px; font-size:.78rem; color:{INK3}; line-height:1.6;}}
  div[data-testid="stTabs"] [data-baseweb="tab-list"] {{gap:6px; border-bottom:1px solid {BORDER};}}
  div[data-testid="stTabs"] button p {{font-size:.95rem; font-weight:600;}}
  .mhint {{display:none;}}
  @media (max-width:768px) {{
    .block-container {{padding:3.2rem .8rem 2rem;}} .hero {{padding:18px;}} .hero h1 {{font-size:1.4rem;}}
    .hero p {{font-size:.9rem;}} .kpis {{grid-template-columns:repeat(2,1fr); gap:8px;}} .kpi {{min-height:0; padding:12px;}}
    .kpi .v {{font-size:1.35rem;}} .kpi .s {{font-size:.74rem;}} .mhint {{display:block; font-size:.78rem; margin-top:10px;}}
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {{overflow-x:auto; flex-wrap:nowrap;}}
    div[data-testid="stTabs"] button {{white-space:nowrap; padding:8px;}} div[data-testid="stTabs"] button p {{font-size:.85rem;}}
  }}
</style>""", unsafe_allow_html=True)
try:
    MOBILE = any(t in (st.context.headers.get("User-Agent") or "") for t in ("Mobi", "Android", "iPhone"))
except Exception:  # noqa: BLE001
    MOBILE = False
CFG = {"displayModeBar": False}


def kpis(items):
    st.markdown('<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="l">{a}</div><div class="v">{b}<span>{c}</span></div><div class="s">{d}</div></div>'
        for a, b, c, d in items) + "</div>", unsafe_allow_html=True)


def section(t, sub=""):
    st.markdown(f'<div class="sec">{t}</div>' + (f'<div class="sec-sub">{sub}</div>' if sub else ""), unsafe_allow_html=True)


def style(fig, title, sub=None, h=360, legend=False):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>" + (f"<br><span style='font-size:12px;color:{INK2};font-weight:400'>{sub}</span>"
                                             if sub else ""), x=0, font=dict(size=15, color=INK)),
        height=h, margin=dict(l=6, r=24, t=74 if sub else 48, b=(80 if MOBILE else 56) if legend else 8), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(color=INK2, size=12), barcornerradius=4,
        hoverlabel=dict(bgcolor="white", bordercolor=BORDER, font=dict(color=INK)), showlegend=legend,
        legend=dict(orientation="h", y=-0.1, yanchor="top", x=0, font=dict(size=11 if MOBILE else 12)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER)
    return fig


@st.cache_data
def base():
    return benchmarks(), mix(), ssa_latest(2023), protection(), cata_curve(), load()


B, MIX, SSA, PROT, (CFIT, CDAT), MODELS = base()
rank_oop, n_ssa = nigeria_rank("oop_share")
rank_bud, _ = nigeria_rank("gov_budget_share", higher_is_worse=False)
last_p = PROT.iloc[-1]

with st.sidebar:
    st.markdown("### 🩺 About")
    st.caption("Health-financing analysis of Nigeria using WHO Global Health Expenditure Database and World Bank data "
               "(2000–2023), with a funding-gap simulator.")
    st.link_button("Code, data & method on GitHub", REPO, width="stretch")
    st.caption("Built by **Daniel Oyewale** · Petgrave.io")

st.markdown(f"""<div class="hero"><div class="eyebrow">Health financing · Nigeria · Universal health coverage</div>
<h1>Who pays for healthcare in Nigeria?</h1>
<p>Mostly, the patient. Households pay {B['oop_share']:.0f}% of all health spending directly, the highest share in
sub-Saharan Africa. This dashboard shows where the money comes from, what it does to families, whether more public money
buys better health, and what closing the gap would cost.</p>
<div class="meta"><span class="chip">Latest data: {B['year']}</span><span class="chip">{n_ssa} African peers</span>
<span class="chip">Source: WHO GHED · World Bank</span></div>
<div class="mhint">Swipe the tabs to explore; the simulator is in the last-but-one tab.</div></div>""", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Africa comparison", "Financial protection", "Does money buy health?", "Funding-gap simulator",
                "Method & data"])

# ============================================================================= OVERVIEW
with tabs[0]:
    st.markdown(f'<div class="headline">In {B["year"]}, Nigeria spent about <b>${B["che_pc_usd"]:.0f} per person</b> on health. '
                f'<b>${B["che_pc_usd"] * B["oop_share"] / 100:.0f}</b> of it came straight from patients\' pockets and only '
                f'<b>${B["gov_pc_usd"]:.0f}</b> from government. Health gets <b>{B["gov_budget_share"]:.1f}%</b> of the '
                f'government budget, against the Abuja target of {ABUJA}%.</div>', unsafe_allow_html=True)
    kpis([("Out-of-pocket share", f"{B['oop_share']:.0f}", "%", f"#{rank_oop} highest of {n_ssa} in sub-Saharan Africa · safe band ≤{OOP_SAFE}%"),
          ("Budget share for health", f"{B['gov_budget_share']:.1f}", "%", f"Abuja target {ABUJA}% · #{rank_bud} lowest of {n_ssa}"),
          ("Government spend / person", f"${B['gov_pc_usd']:.0f}", "", f"benchmark ≈ ${B['gov_pc_target_usd']:.0f} (US$86 in 2015 prices)"),
          ("Catastrophic health costs", f"{last_p.cata10:.1f}", "%", f"of people spent >10% of their budget on health ({int(last_p.year)}) "
                                                                    f"≈ {last_p.cata10 / 100 * last_p.population / 1e6:.0f}M people"),
          ("Under-5 mortality", f"{B['u5mr']:.0f}", "", f"deaths per 1,000 live births · maternal {B['mmr']:,.0f} per 100,000")])
    a, b = st.columns([1.5, 1], gap="large")
    with a:
        fig = go.Figure()
        for c, lab in SOURCES:
            fig.add_trace(go.Scatter(x=MIX.year, y=MIX[c], name=lab.split(" (")[0], stackgroup="one", mode="lines",
                                     line=dict(width=0.5, color="white"), fillcolor=COL[c],
                                     hovertemplate=f"{lab}: %{{y:.1f}}%<extra>%{{x}}</extra>"))
        style(fig, "Where Nigeria's health money comes from", "Share of current health expenditure; each year sums to 100%",
              h=420, legend=True)
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig, width="stretch", config=CFG, key="mix")
    with b:
        msgs = [("Households carry the system", f"Out-of-pocket payments have stayed between {MIX[MIX.year >= 2005].oop_share.min():.0f}% and "
                                               f"{MIX.oop_share.max():.0f}% of health spending since 2005, and the government share fell "
                                               f"from {MIX.gov_share.iloc[0]:.0f}% to {MIX.gov_share.iloc[-1]:.0f}%."),
                ("It pushes families into hardship", f"{last_p.cata10:.0f}% of Nigerians spent more than a tenth of their household "
                                                    "budget on health in the last survey. Countries with lower out-of-pocket shares "
                                                    "have far fewer such families."),
                ("Money alone isn't enough", "Across Africa, how much a government spends isn't robustly linked to child "
                                             "deaths. How much patients pay at the point of care is."),
                ("The Abuja target is affordable-ish", "Reaching 15% of the budget means ~$5.4bn a year more (1.5% of GDP), "
                                                      "and could roughly halve catastrophic spending.")]
        st.markdown('<div class="card"><h4>Key findings</h4>' + "".join(
            f'<div class="msg"><div class="n">{i}</div><div><div class="t">{t}</div><div class="b">{html.escape(b_)}</div></div></div>'
            for i, (t, b_) in enumerate(msgs, 1)) + "</div>", unsafe_allow_html=True)

# ============================================================================= AFRICA COMPARISON
with tabs[1]:
    a, b = st.columns([1.3, 1], gap="large")
    with a:
        d = SSA.copy()
        d["is_ng"] = d.iso3 == "NGA"
        fig = go.Figure()
        for flag, col, size in ((False, "#9ec5f4", 10), (True, ORANGE, 18)):
            dd = d[d.is_ng == flag]
            fig.add_trace(go.Scatter(x=dd.gov_pc_usd, y=dd.oop_share, mode="markers+text" if flag else "markers",
                                     text=dd.name if flag else None, textposition="middle right",
                                     textfont=dict(color=INK, size=13), customdata=np.c_[dd.name, dd.year],
                                     marker=dict(size=size, color=col, line=dict(color="white", width=1.5)),
                                     hovertemplate="%{customdata[0]} (%{customdata[1]})<br>Gov: $%{x:.0f}/person<br>"
                                                   "OOP: %{y:.0f}%<extra></extra>"))
        fig.add_hrect(y0=15, y1=OOP_SAFE, fillcolor=AQUA, opacity=0.12, line_width=0)
        fig.add_annotation(x=0.02, xref="paper", y=17.5, text="15–20%: hardship negligible", showarrow=False,
                           font=dict(color="#0f6b4b", size=11), xanchor="left")
        style(fig, "Government spending vs out-of-pocket share", f"{len(d)} sub-Saharan countries, 2023 or latest", h=440)
        fig.update_xaxes(type="log", title="Government health spending per person (US$, log)", tickprefix="$")
        fig.update_yaxes(title="Out-of-pocket, % of health spending", ticksuffix="%")
        st.plotly_chart(fig, width="stretch", config=CFG, key="peers")
    with b:
        rk = SSA.sort_values("oop_share", ascending=False).head(12)
        fig = go.Figure(go.Bar(y=rk.name[::-1], x=rk.oop_share[::-1], orientation="h",
                               marker_color=[ORANGE if i == "NGA" else "#9ec5f4" for i in rk.iso3[::-1]],
                               text=[f"{v:.0f}%" for v in rk.oop_share[::-1]], textposition="outside", cliponaxis=False,
                               textfont=dict(color=INK2)))
        style(fig, "Highest out-of-pocket shares", "Sub-Saharan Africa, % of health spending", h=440)
        fig.update_xaxes(range=[0, 90], ticksuffix="%")
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config=CFG, key="rank")
    section("Nigeria against the financing benchmarks")
    bm = [("Out-of-pocket share", B["oop_share"], OOP_SAFE, "%", "≤"), ("Health share of government budget", B["gov_budget_share"], ABUJA, "%", "≥"),
          ("Government health spending, % of GDP", B["gov_gdp"], GOV_GDP, "%", "≥"),
          ("Government health spending per person", B["gov_pc_usd"], B["gov_pc_target_usd"], "$", "≥")]
    kpis([(n, f"{'$' if u == '$' else ''}{v:.1f}{'' if u == '$' else '%'}", "", f"target {op} {'$' if u == '$' else ''}{t:.0f}"
          f"{'' if u == '$' else '%'} · {'met' if (v <= t if op == '≤' else v >= t) else f'gap {abs(t - v):.1f}' + ('' if u == '$' else ' pts')}")
          for n, v, t, u, op in bm])

# ============================================================================= FINANCIAL PROTECTION
with tabs[2]:
    a, b = st.columns(2, gap="large")
    with a:
        fig = go.Figure()
        for c, lab, col in (("cata10", ">10% of household budget", ORANGE), ("cata25", ">25% of household budget", NAVY)):
            fig.add_trace(go.Scatter(x=PROT.year, y=PROT[c], name=lab, mode="lines+markers", line=dict(color=col, width=2.5),
                                     marker=dict(size=8), hovertemplate=f"{lab}: %{{y:.1f}}%<extra>%{{x}}</extra>"))
        style(fig, "Nigerians facing catastrophic health costs", "% of population, household surveys (SDG 3.8.2)", h=380, legend=True)
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        st.plotly_chart(fig, width="stretch", config=CFG, key="cata")
    with b:
        x = np.linspace(0, 85, 100)
        other = CDAT[CDAT.iso3 != "NGA"]
        fig = go.Figure([go.Scatter(x=other.oop_share, y=other.cata10, mode="markers", customdata=other.name,
                                    marker=dict(size=8, color="#9ec5f4", line=dict(color="white", width=1)),
                                    hovertemplate="%{customdata}: OOP %{x:.0f}% · %{y:.1f}% catastrophic<extra></extra>"),
                         go.Scatter(x=x, y=np.exp(CFIT["a"] + CFIT["b"] * x), mode="lines", line=dict(color=BLUE, width=2.5),
                                    hoverinfo="skip")])
        ng = CDAT[CDAT.iso3 == "NGA"]
        if len(ng):
            fig.add_trace(go.Scatter(x=ng.oop_share, y=ng.cata10, mode="markers+text", text=["Nigeria"], textposition="top left",
                                     marker=dict(size=15, color=ORANGE, line=dict(color="white", width=1.5)),
                                     textfont=dict(color=INK), hoverinfo="skip"))
        style(fig, "Higher out-of-pocket share, more catastrophic spending",
              f"{CFIT['n']} countries, latest survey since 2010 · fit R² = {CFIT['r2']:.2f}", h=380)
        fig.update_xaxes(title="Out-of-pocket, % of health spending", ticksuffix="%")
        fig.update_yaxes(title="People spending >10% of budget on health", ticksuffix="%")
        st.plotly_chart(fig, width="stretch", config=CFG, key="curve")
    st.markdown(f'<div class="muted">Each 10-point fall in the out-of-pocket share is associated with about '
                f'{(1 - np.exp(-10 * CFIT["b"])):.0%} fewer people facing catastrophic costs (cross-country, log-linear). '
                f'Nigeria\'s last survey ({int(last_p.year)}) found {last_p.cata10:.1f}% above 10% and {last_p.cata25:.1f}% '
                f'above 25% of their budget.</div>', unsafe_allow_html=True)

# ============================================================================= DOES MONEY BUY HEALTH?
with tabs[3]:
    section("Is more public money linked to fewer child deaths?",
            "Three ways of comparing 46 sub-Saharan countries, each controlling for GDP per capita. Associations, not causal effects.")
    specs = [("main", "Within-country, year to year (two-way fixed effects)"), ("long_difference", "Long-run change, 2000–04 → 2018–22"),
             ("cross_section", "Between countries, 2018–22")]
    rows = []
    for k, lab in specs:
        for var, vlab, sc in (("ln_gov_pc", "Government spending ×2", np.log(2)), ("oop10", "Out-of-pocket share +10 pts", 1)):
            c = MODELS[k]["u5mr"]["coef"][var]
            rows.append({"spec": lab, "var": vlab, "est": (np.exp(c["b"] * sc) - 1) * 100,
                         "lo": (np.exp(c["lo"] * sc) - 1) * 100, "hi": (np.exp(c["hi"] * sc) - 1) * 100, "p": c["p"]})
    cf = pd.DataFrame(rows)
    cols = st.columns(2, gap="large")
    for col, vlab in zip(cols, ["Government spending ×2", "Out-of-pocket share +10 pts"]):
        d = cf[cf["var"] == vlab].iloc[::-1]
        fig = go.Figure()
        for _, r in d.iterrows():
            colr = ORANGE if r.p < 0.05 else "#7e8aa3"
            fig.add_trace(go.Scatter(x=[r.lo, r.hi], y=[r.spec, r.spec], mode="lines", line=dict(color=colr, width=4),
                                     hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[r.est], y=[r.spec], mode="markers+text", text=[f"{r.est:+.1f}%{' *' if r.p < .05 else ''}"],
                                     textposition="top center", marker=dict(size=12, color=colr, line=dict(color="white", width=2)),
                                     textfont=dict(color=INK), hovertemplate=f"{r.est:+.1f}% [{r.lo:+.1f}, {r.hi:+.1f}] · p = {r.p:.3f}<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=INK2, dash="dash", width=1))
        style(fig, vlab, "Change in under-5 mortality, 95% CI · orange * = significant at 5%", h=330)
        fig.update_xaxes(ticksuffix="%")
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10 if MOBILE else 12))
        col.plotly_chart(fig, width="stretch", config=CFG, key=f"coef_{vlab}")
    st.markdown('<div class="card"><h4>What this means</h4><div class="muted">The <b>level</b> of government health spending is not '
                'robustly linked to child mortality: none of the three estimates is significant, and they point in different '
                'directions. A higher <b>out-of-pocket share</b> is linked to higher child mortality in two of three '
                'specifications. Read together: extra public money matters for health when it <b>replaces</b> what families '
                'pay at the point of care (financial protection and access), not simply because the budget line is larger. '
                'Fixed effects remove stable country traits and shared shocks, but not every confounder, so these are not '
                'causal estimates.</div></div>', unsafe_allow_html=True)
    with st.expander("Full coefficient table (within-country models, all outcomes)"):
        st.dataframe(table(MODELS["main"]).round(3), hide_index=True, width="stretch")

# ============================================================================= SIMULATOR
with tabs[4]:
    section("What would it take?", "Choose a target and assumptions. Per year, 2023 US$ and today's naira.")
    c1, c2, c3, c4 = st.columns(4)
    kind = c1.selectbox("Public-financing target", TARGETS)
    custom = c1.number_input("Government spend per person (US$)", 10.0, 200.0, 30.0, 1.0) if kind == "Custom" else None
    theta = c2.slider("Share of new public money that replaces patient payments", 0.2, 0.9, 0.6, 0.05,
                      help="θ. 1.0 = every new naira displaces a naira of out-of-pocket spending; lower = more new services.")
    floor = c3.slider("Out-of-pocket floor (copayments, uncovered care)", 0.05, 0.30, 0.15, 0.01, format="%.2f")
    fx = c4.number_input("Exchange rate (₦ per US$)", 500, 3000, FX_DEFAULT, 50)
    r = simulate(kind, theta, fx, custom, floor)
    kpis([("Extra public spending", f"${r.total_usd / 1e9:,.1f}", "bn/yr", f"₦{r.total_ngn / 1e12:,.1f}tn · {r.pct_gdp:.1f}% of GDP · "
                                                                           f"{r.multiple_of_fed_health:.1f}× the 2025 federal health budget"),
          ("Per person", f"${r.gov_pc0:.0f}→${r.gov_pc1:.0f}", "", "government health spending per person"),
          ("Out-of-pocket share", f"{r.oop_share0:.0f}%→{r.oop_share1:.0f}%", "", f"government share → {r.gov_share1:.0f}%"
                                                                                  + (" · floor reached" if r.at_floor else "")),
          ("Catastrophic spending", f"{r.cata0:.1f}→{r.cata1:.1f}", "%", f"range {r.cata1_lo:.1f}–{r.cata1_hi:.1f}% · "
                                                                        f"≈{r.people_protected / 1e6:.0f}M fewer people"),
          ("Child deaths (indicative)", f"{r.deaths_averted_lo / 1e3:,.0f}k–{r.deaths_averted_hi / 1e3:,.0f}k", "", "fewer under-5 deaths a year, "
                                                                                                       "if associations hold")])
    if r.effect_extrapolated:
        st.markdown(f'<div class="warn">⚠️ This scenario changes the out-of-pocket share by {abs(r.oop_share1 - r.oop_share0):.0f} '
                    f'points, more than any African country achieved between 2000 and 2022 (max {max_observed_oop_change():.0f}). '
                    'The mortality range is an extrapolation; treat it as illustrative.</div>', unsafe_allow_html=True)
    a, b = st.columns(2, gap="large")
    with a:
        names = ["Today (2023)", "Scenario"]
        gov0, gov1 = r.gov_pc0, r.gov_pc1
        oop0, oop1 = r.oop_pc0, r.oop_pc1
        rest0 = r.che_pc0 - gov0 - oop0
        fig = go.Figure([go.Bar(name="Government", y=names, x=[gov0, gov1], orientation="h", marker_color=BLUE),
                         go.Bar(name="Out-of-pocket", y=names, x=[oop0, oop1], orientation="h", marker_color=ORANGE),
                         go.Bar(name="Donors & other private", y=names, x=[rest0, rest0], orientation="h", marker_color=GREY)])
        style(fig, "Health spending per person, by source", "US$ per person per year (2023 prices)", h=340, legend=True)
        fig.update_layout(barmode="stack")
        fig.update_xaxes(tickprefix="$")
        fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch", config=CFG, key="sim_mix")
    with b:
        src = [("2025 federal health budget", FED_HEALTH_2025), ("36 states' 2025 health budgets", STATES_HEALTH_2025),
               ("Doubling BHCPF (1% → 2% of CRF)", BHCPF_2025), ("Gap to 15% of the 2025 federal budget",
                                                                 0.15 * FED_BUDGET_2025 - FED_HEALTH_2025)]
        fig = go.Figure(go.Bar(y=[s[0] for s in src][::-1] + ["This scenario needs"], x=[s[1] / 1e12 for s in src][::-1] + [r.total_ngn / 1e12],
                               orientation="h", marker_color=[GREY] * 4 + [NAVY],
                               text=[f"₦{s[1] / 1e12:,.2f}tn" for s in src][::-1] + [f"₦{r.total_ngn / 1e12:,.1f}tn"],
                               textposition="outside", cliponaxis=False, textfont=dict(color=INK)))
        style(fig, "Scale: the gap against today's budgets", "Naira trillions per year; context figures from 2025 budgets", h=300)
        fig.update_xaxes(range=[0, max(r.total_ngn / 1e12, 6.5) * 1.35])
        fig.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10 if MOBILE else 12))
        st.plotly_chart(fig, width="stretch", config=CFG, key="sim_scale")
    st.caption("Mechanics: ΔG = target − today; OOP falls by θ·ΔG, but never below the floor; catastrophic spending is shifted "
               "from Nigeria's last survey along the cross-country gradient (95% CI); child deaths use the OOP-share coefficient "
               "(low = within-country estimate, not significant; high = long-run estimate) × births × under-5 mortality. "
               "Costs are in 2023 US$ and converted at the chosen rate.")

# ============================================================================= METHOD
with tabs[5]:
    a, b = st.columns(2, gap="large")
    a.markdown("""
#### Data
- **WHO Global Health Expenditure Database**, via the World Bank *Health Nutrition and Population Statistics* bulk file
  (CC BY 4.0): health spending by source, SDG 3.8.2 catastrophic spending, under-5 and maternal mortality, UHC index.
- **World Bank WDI**: GDP per capita, PPP (constant 2021 $).
- **Benchmarks:** WHO World Health Report 2010 (OOP 15–20%), Abuja Declaration 2001 (15%), McIntyre et al. 2017
  (5% of GDP; US$86 per person).
- **Nigeria 2025 context:** approved federal budget ₦54.99tn with ₦2.38tn for health (4.33%); states ₦2.36tn; BHCPF ₦283bn;
  NHIA 21.7M enrollees (≈10%).

#### Models
- Two-way fixed effects panel (46 SSA countries, 2000–2023), clustered SEs, spending lagged one year; robustness checks
  without the lag, excluding Nigeria, and without the OOP term.
- Long-difference (2000–04 → 2018–22) and cross-section (2018–22) models for comparison.
""")
    b.markdown("""
#### Limitations
- **Associations, not causal effects.** Spending responds to health needs, and mortality series are modelled estimates.
- Catastrophic-spending surveys are infrequent (Nigeria's latest: 2018). The cross-country fit explains about a fifth of
  the variation.
- The simulator holds everything else constant: no GDP growth, no change in prices, no efficiency gains or leakages.
- θ (substitution of public for private money) and the OOP floor are assumptions, so test them with the sliders.
- 2023 dollar figures are converted at a 2025 exchange rate to approximate today's naira.
""")
    with st.expander("Sources and assumptions table"):
        st.dataframe(pd.read_csv(ROOT / "data" / "reference" / "assumptions.csv"), hide_index=True, width="stretch")

st.markdown(f'<div class="foot">Data: WHO Global Health Expenditure Database and World Bank (CC BY 4.0). Analysis for '
            f'research and advocacy; not official statistics. · <a href="{REPO}">Code &amp; method</a> · Built by Daniel '
            'Oyewale, Petgrave.io</div>', unsafe_allow_html=True)
