# Architecture

## Diagrams

- `star_schema_er.drawio`: DWD layer ER diagram. It shows `dwd.dim_vehicle`, `dwd.dim_station`, `dwd.fact_charge_order`, `dwd.fact_payment`, and `dwd.fact_station_ops`.
- `architecture_pipeline.drawio`: end-to-end data pipeline diagram from raw CSV sources to ODS, DWD, DWS, ADS, FEATURE, SERVING, MONITOR, and exported CSV outputs.

## Layered Design

1. ODS (`ods_*`): raw ingestion from source systems.
2. DWD (`dwd_*`): cleaned fact/dimension with standard types and keys.
3. DWS (`dws_*`): aggregated service metrics by station and vehicle.
4. ADS (`ads_*`): business-facing supply-demand and efficiency indicators.
5. FEATURE (`feature_*`): model/strategy wide table.
6. SERVING (`serving_*`): top-N recommendation output.
7. MONITOR (`monitor_*`): quality and freshness checks.

## Spark / Kafka Extension Architecture

The current implementation is a local, reproducible DuckDB demo. In a production-like environment, the same layered design can be extended with Kafka and Spark.

```text
EV App / Charging Station / Payment System / Ops Platform
					 ↓
				 Kafka Topics
					 ↓
 Spark Structured Streaming + Spark Batch
					 ↓
 ODS → DWD → DWS → ADS → FEATURE → SERVING → MONITOR
					 ↓
 Recommendation API / BI Dashboard / Quality Alerts
```

### Kafka Responsibilities

Kafka can replace static CSV ingestion with event-driven data collection:

| Topic | Example events | Target layer |
|---|---|---|
| `vehicle_profile_events` | vehicle registration, profile update | ODS vehicle profile |
| `charger_station_events` | station onboarding, tariff update, port update | ODS station profile |
| `charge_order_events` | order created, charging started, completed | ODS charge order |
| `payment_txn_events` | payment success, refund, payment failure | ODS payment transaction |
| `station_ops_snapshot_events` | online rate, queue minutes, fault count | ODS station ops snapshot |

Kafka brings three main benefits:

- decouples source systems from downstream data jobs
- supports near real-time ingestion for fast-changing station status
- provides replay capability for rebuilding downstream tables

### Spark Responsibilities

Spark can scale the SQL pipeline from single-machine analytics to large-scale batch and streaming jobs:

| Current DuckDB step | Spark production extension |
|---|---|
| CSV to ODS | Kafka stream to ODS tables or data lake files |
| DWD cleansing | Spark jobs standardize schemas, types, and keys |
| DWS aggregation | Spark computes 7-day station metrics and 30-day vehicle preference windows |
| ADS scoring | Spark calculates station operability and supply-demand scores |
| FEATURE wide table | Spark generates large vehicle-station candidate features |
| SERVING Top-N | Spark ranks candidates and exports recommendation results |
| MONITOR checks | Spark or SQL quality checks generate alerts and reports |

### Batch + Streaming Split

A practical production split is:

- **Streaming path**: Kafka + Spark Structured Streaming updates station status, queue pressure, recent orders, and payment events every few minutes.
- **Batch path**: Spark Batch rebuilds historical features, 7-day/30-day aggregates, and Top-N recommendation candidates on an hourly or daily schedule.
- **Serving path**: the latest recommendation table is exported to an API service, cache table, or BI dashboard.

### Why Not Replace DuckDB in This Demo

DuckDB remains useful for the portfolio version because it is lightweight, reproducible, and easy to run locally. Kafka and Spark are best presented as a production extension path rather than required dependencies for the demo.

## Business Goal

Recommend better charging stations for each vehicle by balancing:
- convenience (zone match)
- station capacity and queue
- user historical preference
- estimated charging cost

## Recommendation Score Logic (Demo)

Final score is weighted by:
- preference score from user historical sessions
- station utilization and queue pressure
- tariff competitiveness
- zone matching between vehicle home zone and station zone

Weights are configurable in SQL and can later move to a feature service or strategy engine.
