"""Build a tidy country-year panel from the World Bank HNP bulk file and WDI GDP per capita.

Raw inputs (git-ignored, ~120 MB) go in data/raw/:
  * HNP_Stats_CSV.zip   https://databank.worldbank.org/data/download/HNP_Stats_CSV.zip  (CC BY 4.0)
  * API_NY.GDP.PCAP.PP.KD_DS2_en_csv_v2_*.zip   https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD (CC BY 4.0)
Run:  python src/healthfin/ingest.py
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from healthfin.paths import COUNTRIES, PANEL, PROCESSED, RAW  # noqa: E402

INDICATORS = {
    # health financing (WHO Global Health Expenditure Database via World Bank)
    "SH.XPD.CHEX.PC.CD": "che_pc_usd",          # current health expenditure per capita, current US$
    "SH.XPD.CHEX.PP.CD": "che_pc_ppp",
    "SH.XPD.CHEX.GD.ZS": "che_gdp",             # % of GDP
    "SH.XPD.GHED.CH.ZS": "gov_share",           # domestic general government, % of CHE
    "SH.XPD.GHED.GD.ZS": "gov_gdp",             # % of GDP
    "SH.XPD.GHED.GE.ZS": "gov_budget_share",    # % of general government expenditure (Abuja indicator)
    "SH.XPD.GHED.PC.CD": "gov_pc_usd",
    "SH.XPD.GHED.PP.CD": "gov_pc_ppp",
    "SH.XPD.PVTD.CH.ZS": "pvt_share",           # domestic private, % of CHE (includes OOP)
    "SH.XPD.OOPC.CH.ZS": "oop_share",           # out-of-pocket, % of CHE
    "SH.XPD.OOPC.PC.CD": "oop_pc_usd",
    "SH.XPD.EHEX.CH.ZS": "ext_share",           # external, % of CHE
    # financial protection (SDG 3.8.2) and impoverishment
    "SH.UHC.OOPC.10.ZS": "cata10",              # % population spending >10% of budget on health
    "SH.UHC.OOPC.25.ZS": "cata25",
    "SH.UHC.OOPC.10.TO": "cata10_n",
    "SH.UHC.NOP1.ZS": "impov215",               # % pushed below $2.15/day
    # outcomes and coverage
    "SH.DYN.MORT": "u5mr",                      # under-5 deaths per 1,000 live births
    "SH.STA.MMRT": "mmr",                       # maternal deaths per 100,000 live births (modelled)
    "SH.UHC.SRVS.CV.XD": "uhc_index",           # UHC service coverage index (0-100)
    "SP.DYN.LE00.IN": "life_exp",
    # denominators
    "SP.POP.TOTL": "population",
    "SP.DYN.CBRT.IN": "birth_rate",             # births per 1,000 people
}


def _read_zip_csv(zpath: Path, member_pred, **kw) -> pd.DataFrame:
    with zipfile.ZipFile(zpath) as z:
        name = next(n for n in z.namelist() if member_pred(n))
        return pd.read_csv(io.BytesIO(z.read(name)), **kw)


def load_hnp() -> tuple[pd.DataFrame, pd.DataFrame]:
    z = RAW / "HNP_Stats_CSV.zip"
    data = _read_zip_csv(z, lambda n: n.endswith("StatsCSV.csv"))
    meta = _read_zip_csv(z, lambda n: n.endswith("StatsCountry.csv"))
    return data, meta


def load_gdp() -> pd.DataFrame:
    z = next(RAW.glob("API_NY.GDP.PCAP.PP.KD*.zip"))
    return _read_zip_csv(z, lambda n: n.startswith("API_"), skiprows=4)


def to_long(df: pd.DataFrame, codes: dict) -> pd.DataFrame:
    df = df[df["Indicator Code"].isin(codes)]
    yrs = [c for c in df.columns if str(c).strip().isdigit()]
    long = df.melt(id_vars=["Country Code", "Indicator Code"], value_vars=yrs, var_name="year", value_name="value")
    long = long.dropna(subset=["value"])
    long["year"] = long.year.astype(int)
    long["var"] = long["Indicator Code"].map(codes)
    return long


def build() -> pd.DataFrame:
    hnp, meta = load_hnp()
    gdp = load_gdp()
    long = pd.concat([to_long(hnp, INDICATORS), to_long(gdp, {"NY.GDP.PCAP.PP.KD": "gdp_pc_ppp"})])
    panel = (long.pivot_table(index=["Country Code", "year"], columns="var", values="value", aggfunc="first")
             .reset_index().rename(columns={"Country Code": "iso3"}))
    countries = meta.rename(columns={"Country Code": "iso3", "Short Name": "name", "Region": "region",
                                     "Income Group": "income"})[["iso3", "name", "region", "income"]]
    countries = countries[countries.region.notna()]           # drop aggregates
    panel = panel[panel.iso3.isin(countries.iso3) & panel.year.between(2000, 2024)]
    panel = panel.merge(countries, on="iso3", how="left")
    # derived: the four sources of current health expenditure, which sum to 100%
    panel["other_pvt_share"] = (panel.pvt_share - panel.oop_share).clip(lower=0)
    panel["births"] = panel.birth_rate / 1000 * panel.population
    return panel.sort_values(["iso3", "year"]).reset_index(drop=True), countries


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    panel, countries = build()
    panel.to_parquet(PANEL, index=False)
    countries.to_csv(COUNTRIES, index=False)
    ng = panel[panel.iso3 == "NGA"].set_index("year")
    print(f"panel {panel.shape}, countries {countries.shape[0]}, SSA {countries.region.eq('Sub-Saharan Africa').sum()}")
    print(ng.loc[2018:2023, ["oop_share", "gov_share", "ext_share", "other_pvt_share", "che_pc_usd", "gov_budget_share",
                             "u5mr", "mmr", "gdp_pc_ppp"]].round(2))


if __name__ == "__main__":
    main()
