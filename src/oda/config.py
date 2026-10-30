"""Paths and source definitions. One place to change where data comes from."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
MODELS = ROOT / "models"
QUALITY = ROOT / "quality"

# DATA_MODE=sample uses the small synthetic files committed in data/sample/ (same layout as the real files).
# DATA_MODE=real uses files downloaded by `python -m oda.fetch` into data/raw/ (gitignored).
DATA_MODE = os.getenv("DATA_MODE", "sample").lower()


def raw_dir() -> Path:
    return DATA / ("raw" if DATA_MODE == "real" else "sample")


WAREHOUSE = Path(os.getenv("WAREHOUSE_PATH", DATA / f"warehouse_{DATA_MODE}.duckdb"))

# --- Source 1: NSW Valuer General bulk property sales information (PSI) -----------------------
# Licence: CC BY-NC-ND 4.0 for non-commercial use. Commercial use needs a PSI licence.
# Raw files must NOT be committed to this repo (no-derivatives licence) — fetch them locally.
NSW_PSI_YEARLY_URL = os.getenv(
    "NSW_PSI_YEARLY_URL", "https://www.valuergeneral.nsw.gov.au/__psi/yearly/{year}.zip"
)
NSW_PSI_WEEKLY_URL = os.getenv(
    "NSW_PSI_WEEKLY_URL", "https://www.valuergeneral.nsw.gov.au/__psi/weekly/{yyyymmdd}.zip"
)

# If NSW moves its download addresses, download the yearly/weekly zips by hand from the
# Valuer General's property sales portal into this folder; `python -m oda.fetch --nsw-local`
# (and every NSW fetch) extracts whatever zips it finds here. Portal page:
# https://valuation.property.nsw.gov.au/embed/propertySalesInformation
NSW_MANUAL_DIR = Path(os.getenv("NSW_MANUAL_DIR", DATA / "raw" / "nsw_downloads"))

# Ordered field names for 'B' (sale) records in the post-2001 .DAT layout, semicolon delimited.
NSW_B_FIELDS = [
    "record_type", "district_code", "property_id", "sale_counter", "download_datetime",
    "property_name", "unit_no", "house_no", "street_name", "locality", "postcode",
    "area", "area_type", "contract_date", "settlement_date", "purchase_price",
    "zoning", "nature_of_property", "primary_purpose", "strata_lot_no",
    "component_code", "sale_code", "pct_interest_of_sale", "dealing_no",
]

# --- Source 2: UK DfT vehicle licensing statistics, VEH0160 (first registrations) -------------
# Licence: Open Government Licence v3.0. Quarterly, by body type, make, generic model, model, fuel.
DFT_VEH0160_URL = os.getenv(
    "DFT_VEH0160_URL",
    "https://assets.publishing.service.gov.uk/media/6aad4b1ef1f8d2a39605fa1b/df_VEH0160_UK.csv",
)
