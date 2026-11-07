from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REFERENCE = ROOT / "data" / "reference"
FIGURES = ROOT / "reports" / "figures"

PANEL = PROCESSED / "panel.parquet"
COUNTRIES = PROCESSED / "countries.csv"
MODELS = PROCESSED / "panel_models.json"
ASSUMPTIONS = REFERENCE / "assumptions.csv"
