# TASK.md

Status: `[x]` done · `[ ]` to do

## ✅ Phase 1: Build (done, 2026-11-07)
- [x] Ingest WHO GHED (via World Bank HNP Statistics) + WDI GDP PPP into a 2000–2024 country panel
- [x] Financing mix, benchmarks, SSA ranking, financial protection, catastrophic-spending curve
- [x] Panel models (two-way FE, long-difference, cross-section) + robustness
- [x] Funding-gap simulator (Abuja, 5% GDP, US$86, custom) with OOP floor and extrapolation flags
- [x] Static figures, two-page policy brief (PDF), Streamlit dashboard with mobile layout
- [x] Tests + GitHub Actions CI
- [x] README, AGENTS, MEMORY, TASK

## 🚀 Phase 2: Publish
- [x] Deploy to Streamlit Community Cloud: https://health-financing-nigeria.streamlit.app/
- [ ] Make the repo public, then enable GitHub Pages (Source: GitHub Actions) *(you)*
- [ ] LinkedIn post

## 💡 Backlog (nice to have)
- [ ] State-level view: state health budgets and NHIA/state scheme enrolment
- [ ] Add NLSS 2018/19 and newer household survey OOP data when available
- [ ] Instrumental-variable or synthetic-control check for the spending–mortality link
- [ ] Phased funding path (5-year ramp to Abuja) with federal/state cost split
