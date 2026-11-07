"""Two-page policy brief (PDF).  Run: python -m healthfin.brief"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from .financing import ABUJA, OOP_SAFE, benchmarks, cata_curve, mix, nigeria_rank, protection
from .model import load
from .paths import FIGURES, ROOT
from .simulator import TARGETS, max_observed_oop_change, simulate

OUT = ROOT / "reports" / "policy_brief.pdf"
NAVY, ORANGE, INK2, BORDER = colors.HexColor("#0d366b"), colors.HexColor("#eb6834"), colors.HexColor("#52514e"), colors.HexColor("#e7e5e0")
W = A4[0] - 32 * mm

S = {
    "eyebrow": ParagraphStyle("e", fontName="Helvetica-Bold", fontSize=7.5, textColor=ORANGE, leading=10, spaceAfter=2),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=NAVY, spaceAfter=4),
    "dek": ParagraphStyle("dek", fontName="Helvetica", fontSize=10, leading=14, textColor=INK2, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="Helvetica", fontSize=9, leading=12.6, spaceAfter=5),
    "bullet": ParagraphStyle("bl", fontName="Helvetica", fontSize=9, leading=12.6, leftIndent=10, bulletIndent=0, spaceAfter=3),
    "small": ParagraphStyle("s", fontName="Helvetica", fontSize=7, leading=9.2, textColor=INK2),
    "kl": ParagraphStyle("kl", fontName="Helvetica-Bold", fontSize=6.8, leading=8, textColor=INK2),
    "kv": ParagraphStyle("kv", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=colors.black),
    "ks": ParagraphStyle("ks", fontName="Helvetica", fontSize=6.8, leading=8.4, textColor=INK2),
}


def _kpis(items):
    cells = [[Paragraph(a.upper(), S["kl"]), Paragraph(b, S["kv"]), Paragraph(c, S["ks"])] for a, b, c in items]
    t = Table([cells], colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, BORDER), ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def _img(name, width):
    p = FIGURES / name
    from PIL import Image as PImage
    w, h = PImage.open(p).size
    return Image(str(p), width=width, height=width * h / w)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(INK2)
    canvas.drawString(16 * mm, 10 * mm, "Who pays for healthcare in Nigeria? · Daniel Oyewale · "
                                        "github.com/Engr-Daniel/health-financing-nigeria")
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"{doc.page}/2")
    canvas.restoreState()


def build(out=OUT):
    b, m, prot, models = benchmarks(), mix(), protection(), load()
    fit, _ = cata_curve()
    last = prot.iloc[-1]
    rank, n = nigeria_rank("oop_share")
    ab, gdp5, pc86 = (simulate(k) for k in TARGETS[:3])
    ld = models["long_difference"]["u5mr"]["coef"]["oop10"]
    fe_gov = models["main"]["u5mr"]["coef"]["ln_gov_pc"]
    oop_usd = b["che_pc_usd"] * b["oop_share"] / 100

    st = []
    st += [Paragraph("POLICY BRIEF · HEALTH FINANCING · NIGERIA", S["eyebrow"]),
           Paragraph("Who pays for healthcare in Nigeria?", S["h1"]),
           Paragraph(f"Mostly, the patient. In {b['year']} households paid {b['oop_share']:.0f}% of all health spending out of "
                     f"pocket, the highest share of {n} countries in sub-Saharan Africa. Public money that replaces those payments, "
                     "not simply a bigger budget line, is what the evidence links to fewer families in hardship and fewer child deaths.",
                     S["dek"]),
           _kpis([("Out-of-pocket share", f"{b['oop_share']:.0f}%", f"#{rank} of {n} in SSA · safe band 15-{OOP_SAFE}%"),
                  ("Health share of budget", f"{b['gov_budget_share']:.1f}%", f"Abuja target {ABUJA}%"),
                  ("Govt spend per person", f"${b['gov_pc_usd']:.0f}", f"benchmark about ${b['gov_pc_target_usd']:.0f}"),
                  ("Catastrophic costs", f"{last.cata10:.1f}%", f">10% of budget ({int(last.year)}), about "
                                                                f"{last.cata10 / 100 * last.population / 1e6:.0f}M people"),
                  ("Under-5 mortality", f"{b['u5mr']:.0f}", "per 1,000 live births")]),
           Spacer(1, 6),
           Paragraph("1. Households carry the system", S["h2"]),
           Paragraph(f"Nigeria spent about ${b['che_pc_usd']:.0f} per person on health in {b['year']}: ${oop_usd:.0f} from patients' "
                     f"pockets, ${b['gov_pc_usd']:.0f} from government, the rest from donors and other private sources. The "
                     f"out-of-pocket share has stayed between {m[m.year >= 2005].oop_share.min():.0f}% and {m.oop_share.max():.0f}% "
                     f"since 2005, while the government share slipped from {m.gov_share.iloc[0]:.0f}% to {m.gov_share.iloc[-1]:.0f}%. "
                     f"Health receives {b['gov_budget_share']:.1f}% of government spending, about a third of the {ABUJA}% that Nigeria "
                     "committed to in Abuja in 2001.", S["body"]),
           _img("01_financing_mix.png", W * 0.92),
           Paragraph("2. Paying at the point of care pushes families into hardship", S["h2"]),
           Paragraph(f"In the {int(last.year)} household survey, {last.cata10:.1f}% of Nigerians spent more than a tenth of their "
                     f"household budget on health and {last.cata25:.1f}% more than a quarter. Across {fit['n']} countries, each "
                     f"10-point fall in the out-of-pocket share goes with about {(1 - 2.718281828 ** (-10 * fit['b'])):.0%} fewer "
                     "people facing catastrophic costs.", S["body"]),
           _img("03_catastrophic_vs_oop.png", W * 0.62),
           ]
    st.append(PageBreak())
    st += [Paragraph("3. Does more public money buy better health?", S["h2"]),
           Paragraph(f"Not on its own. In a panel of 46 African countries (2000–2023), year-to-year changes in government health "
                     f"spending are not significantly linked to under-5 mortality (p = {fe_gov['p']:.2f}). The out-of-pocket share is: "
                     f"over the long run, countries whose out-of-pocket share fell by 10 points saw under-5 mortality about "
                     f"{(2.718281828 ** (ld['b']) - 1):.0%} lower than otherwise (p = {ld['p']:.3f}), controlling for income. These are "
                     "associations, not causal estimates.", S["body"]),
           _img("04_what_drives_child_mortality.png", W * 0.92),
           Paragraph("4. What would it cost?", S["h2"])]
    hs = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7.4, leading=9, textColor=colors.white)
    rows = [[Paragraph(h, hs) for h in ("Target", "Extra per year", "% of GDP", "Out-of-pocket share", "Catastrophic spending",
                                        "Fewer under-5 deaths a year")]]
    for r in (ab, gdp5, pc86):
        rows.append([r.target.replace(" (2015 $)", ""), f"${r.total_usd / 1e9:.1f}bn\n(N{r.total_ngn / 1e12:.1f}tn)",
                     f"{r.pct_gdp:.1f}%", f"{r.oop_share0:.0f}% → {r.oop_share1:.0f}%" + (" (floor)" if r.at_floor else ""),
                     f"{r.cata0:.1f}% → {r.cata1:.1f}%", f"{r.deaths_averted_lo / 1e3:.0f}k–{r.deaths_averted_hi / 1e3:.0f}k"
                     + (" *" if r.effect_extrapolated else "")])
    t = Table(rows, colWidths=[W * f for f in (0.25, 0.14, 0.09, 0.18, 0.16, 0.18)])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 7.8), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.4),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                           ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#fdf0ea")),
                           ("GRID", (0, 0), (-1, -1), 0.4, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    st += [t, Spacer(1, 3),
           Paragraph(f"Assumes 60% of new public money replaces patient payments, an out-of-pocket floor of 15%, 2023 prices and "
                     f"₦1,500/US$. * Out-of-pocket change larger than any African country achieved in 2000–2022 "
                     f"(max {max_observed_oop_change():.0f} points); mortality effect extrapolated. Catastrophic baseline = {int(last.year)} survey "
                     f"value adjusted to the {b['year']} out-of-pocket share along the cross-country curve.".replace("₦", "N"), S["small"]),
           Paragraph("5. Recommendations", S["h2"])]
    recs = [f"<b>Fund the Abuja target in stages.</b> Reaching {ABUJA}% of the budget costs about ${ab.total_usd / 1e9:.1f}bn a year "
            f"({ab.pct_gdp:.1f}% of GDP, {ab.multiple_of_fed_health:.1f}× the 2025 federal health budget). Phase it in over five "
            "years, sharing the cost between federal and state governments.",
            "<b>Spend it on replacing fees, not adding line items.</b> Route new money through the Basic Health Care Provision "
            "Fund and state insurance schemes to remove user fees for primary care, maternal and child services first.",
            "<b>Pool, then purchase.</b> Insurance covers about 10% of Nigerians (21.7M). Make enrolment automatic for the poor, "
            "subsidised by tax, so prepaid money replaces cash at the clinic.",
            "<b>Measure what families pay.</b> The last catastrophic-spending survey is from 2018. Add health-spending questions "
            "to every household survey and publish out-of-pocket share as a budget KPI."]
    st += [Paragraph(r, S["bullet"], bulletText="•") for r in recs]
    st += [Spacer(1, 6), KeepTogether(Paragraph(
        "Data: WHO Global Health Expenditure Database via World Bank HNP Statistics; World Bank WDI (CC BY 4.0). Benchmarks: WHO "
        "World Health Report 2010; Abuja Declaration 2001; McIntyre et al. 2017. Budget context: 2025 Appropriation Act; Nigeria "
        "Governors' Forum; NHIA. Methods, code and an interactive simulator: github.com/Engr-Daniel/health-financing-nigeria.",
        S["small"]))]

    out.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
                      title="Who pays for healthcare in Nigeria? Policy brief", author="Daniel Oyewale").build(
        st, onFirstPage=_footer, onLaterPages=_footer)
    return out


if __name__ == "__main__":
    print(build())
