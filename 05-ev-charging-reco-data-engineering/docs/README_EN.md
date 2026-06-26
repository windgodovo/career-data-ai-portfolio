# EV Charging Replenishment Recommendation - Data Engineering Project

This project is a data-engineering-oriented demo for an automotive charging recommendation scenario.

Core chain:

vehicle / charger / order / payment / operations systems
-> ingestion
-> cleaning and standardization
-> warehouse layered modeling
-> feature wide table
-> recommendation serving
-> monitoring and governance

## Project Structure

- `data/ods_raw/`: raw source tables (CSV mock data)
- `sql/`: layered SQL jobs from ODS to serving
- `scripts/run_pipeline.py`: one-click pipeline runner
- `data/warehouse/charging_reco.duckdb`: local warehouse database
- `data/output/`: exported recommendation and quality reports
- `docs/`: architecture and data contracts

## Quick Start

```bash
cd "05-ev-charging-reco-data-engineering"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
```

## Expected Outputs

- Recommendation result: `data/output/charge_reco_topn.csv`
- Feature table sample: `data/output/vehicle_station_preference_wide.csv`
- Data quality report: `data/output/data_quality_report.csv`

## Who This Is For

This is suitable for a data engineer interview portfolio in charging / replenishment recommendation direction, with clear layering and business metrics lineage.