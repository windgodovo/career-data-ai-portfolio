# Data Contract (Core Tables)

## Source Inputs (ODS Raw CSV)

### vehicle_profile.csv
- `vehicle_id` string
- `user_id` string
- `home_zone` string
- `battery_kwh` double
- `preferred_power_type` string

### charger_station.csv
- `station_id` 
- `station_name` string
- `zone` string
- `power_type` string
- `available_ports` int
- `tariff_cny_per_kwh` double

### charge_order.csv
- `order_id` string
- `vehicle_id` string
- `station_id` string
- `start_time` timestamp
- `end_time` timestamp
- `energy_kwh` double
- `status` string

### payment_txn.csv
- `payment_id` string
- `order_id` string
- `amount_cny` double
- `pay_time` timestamp
- `pay_method` string
- `is_success` int

### station_ops_snapshot.csv
- `station_id` string
- `snapshot_time` timestamp
- `online_rate` double
- `queue_minutes` int
- `fault_count` int

## Key Outputs

### serving.charge_reco_topn
- `vehicle_id`
- `station_id`
- `recommend_score`
- `rank_no`

### monitor.data_quality_report
- `check_item`
- `check_result`
- `detail`

This contract is intentionally compact and suitable for extension to a Kafka + Lakehouse production setup.
