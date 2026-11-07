# MEMORY.md

Long-term project memory: context, decisions and lessons. Newest decisions first.

## Context
- **Owner:** Daniel Oyewale (personal portfolio project; no employer affiliation in this repo). Portfolio project 4 of 5. The others cover carbon accounting, data strategy, solar
  mini-grids and greenwashing detection. Project 4 was rescoped from climate/crops to finance and health.
- **Question:** who pays for healthcare in Nigeria, what does it cost families, does public money buy health, and what
  would closing the gap cost?
- **Data:** the owner uploaded the World Bank HNP Statistics bulk file (WHO GHED inside) and WDI GDP per capita PPP. The
  sandbox cannot download them, so raw zips stay git-ignored and the processed panel is committed.

## Results snapshot (Nigeria, 2023)
- OOP 71.9% of current health expenditure (#1 of 48 SSA); government 14.3%, external 11.3%, other private 2.5%
- Health = 4.3% of government spending (Abuja 15%); 0.6% of GDP; $9.58 per person (benchmark $110.56 = US$86 in 2015 prices)
- Catastrophic spending >10%: 15.8% (2018 survey), down from 22.5% (2003); U5MR 117; MMR 993
- Models (U5MR): gov spending not significant within-country; OOP +10 pp → +2.7% FE (p 0.12), +11.2% long-difference (p 0.035), +7.2% cross-section (p 0.04)
- Abuja scenario (θ 0.6): +$23.8 per person = $5.4bn (~N8.1tn, 1.5% GDP, 3.4× the 2025 federal health budget); OOP 72% → 44%; catastrophic 14.3% → 7.3%; 62k–223k fewer under-5 deaths a year (indicative)

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-07 | Own visual identity for app and site: Public Sans only, white/navy, 'every $100' grid header. Fonts self-hosted (app/static, site/assets/fonts, SIL OFL) | Owner: each project must look distinct, not like a generic template; personal project, so no employer branding |
| 2026-11-07 | Dashboard tabs: Overview → Africa comparison → Financial protection → Does money buy health? → Simulator → Method | Stakeholder story order; mobile via CSS grid + User-Agent switch |
| 2026-11-07 | Policy brief is generated from code (`healthfin.brief`) | Numbers in the brief always match the dashboard |
| 2026-11-07 | Simulator OOP floor (default 15%) plus `at_floor` / `effect_extrapolated` flags | Without a floor, large targets drove OOP to 0%, which is implausible |
| 2026-11-07 | Mortality range = FE coefficient (low) to long-difference coefficient (high) on OOP share | Spending level itself isn't significant; OOP share is the channel the evidence supports |
| 2026-11-07 | Catastrophic spending scaled from Nigeria's 2018 survey along a log-linear cross-country curve (n 142, R² 0.21) | No newer survey; the curve gives a range, not a point |
| 2026-11-07 | θ = 0.6 (share of new public money replacing OOP), slider 0.2–0.9 | Assumption; disclosed and tested |
| 2026-11-07 | 2023 US$ converted at N1,500/US$ (2025 budget assumption) | Approximates today's naira; adjustable |
| 2026-11-07 | Peer group = 48 sub-Saharan countries (World Bank region) | Comparable income and health systems |
