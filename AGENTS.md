# AGENTS.md

Instructions for AI coding agents and human collaborators working in this repository.

## Project at a glance
Health-financing analysis of Nigeria: who pays for healthcare, what out-of-pocket payments do to families, whether public
money is linked to better health across Africa, and what closing the funding gap would cost. It ships a Streamlit
dashboard with a funding-gap simulator and a two-page policy brief. It is a personal portfolio project by Daniel Oyewale.

**Read `MEMORY.md` (context & decisions) and `TASK.md` (priorities) before starting work.**

## Commands
```bash
pip install -r requirements-dev.txt           # dashboard only: requirements.txt
pytest -q                                     # must pass before committing
streamlit run app/streamlit_app.py
PYTHONPATH=src python -m healthfin.ingest     # data/raw/*.zip -> data/processed/panel.parquet
PYTHONPATH=src python -m healthfin.model      # panel models -> data/processed/panel_models.json
PYTHONPATH=src python -m healthfin.figures    # reports/figures/*.png
PYTHONPATH=src python -m healthfin.brief      # reports/policy_brief.pdf
```

## Code map
| Path | Purpose |
|---|---|
| `src/healthfin/ingest.py` | Reads the World Bank HNP Statistics and WDI GDP PPP bulk zips; builds the country-year panel |
| `src/healthfin/financing.py` | Financing mix (sums to 100), benchmarks, SSA ranks, financial protection, catastrophic-spending curve |
| `src/healthfin/model.py` | Two-way FE panel (linearmodels), long-difference and cross-section models (statsmodels) and robustness checks |
| `src/healthfin/simulator.py` | Funding-gap simulator: cost, OOP offset with floor, catastrophic spending, indicative under-5 deaths |
| `src/healthfin/figures.py`, `brief.py` | Static figures and the PDF policy brief |
| `app/streamlit_app.py` | UI only. No calculation logic |
| `data/reference/assumptions.csv` | Every benchmark, budget figure and assumption, with its source |
| `data/processed/` | Committed outputs the app and CI need (keep small) |
| `data/raw/` | Git-ignored source zips (download links in README) |

## Rules
1. **Associations, not causes.** Never describe model coefficients or simulator mortality numbers as causal effects.
2. **Sources:** every number in `assumptions.csv` must cite a source or say "Assumption".
3. **Shares sum to 100.** Any chart of the financing mix must add up to 100% (tested).
4. **Logic in `src/`.** The app and brief import from `healthfin` and never re-implement formulas.
5. **Flag extrapolation.** If a scenario hits the OOP floor or moves OOP beyond what any African country achieved, the UI must say so.
6. **Keep `requirements.txt` minimal:** Streamlit Cloud installs it. matplotlib, reportlab and pytest go in `requirements-dev.txt`.
7. **After each session:** update `TASK.md` and record decisions in `MEMORY.md`.

## Commit conventions
`feat:`, `fix:`, `docs:`, `data:`, `test:`, `refactor:`, `chore:`.

## Git attribution
Never add `Co-Authored-By`, `Claude-Session` or other AI attribution lines to commits or PRs (see CLAUDE.md).
