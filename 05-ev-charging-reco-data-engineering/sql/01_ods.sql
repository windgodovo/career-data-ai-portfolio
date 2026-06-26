CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dwd;
CREATE SCHEMA IF NOT EXISTS dws;
CREATE SCHEMA IF NOT EXISTS ads;
CREATE SCHEMA IF NOT EXISTS feature;
CREATE SCHEMA IF NOT EXISTS serving;
CREATE SCHEMA IF NOT EXISTS monitor;

CREATE OR REPLACE TABLE ods.vehicle_profile AS
SELECT * FROM read_csv_auto('{{ROOT}}/data/ods_raw/vehicle_profile.csv', header = true);

CREATE OR REPLACE TABLE ods.charger_station AS
SELECT * FROM read_csv_auto('{{ROOT}}/data/ods_raw/charger_station.csv', header = true);

CREATE OR REPLACE TABLE ods.charge_order AS
SELECT * FROM read_csv_auto('{{ROOT}}/data/ods_raw/charge_order.csv', header = true);

CREATE OR REPLACE TABLE ods.payment_txn AS
SELECT * FROM read_csv_auto('{{ROOT}}/data/ods_raw/payment_txn.csv', header = true);

CREATE OR REPLACE TABLE ods.station_ops_snapshot AS
SELECT * FROM read_csv_auto('{{ROOT}}/data/ods_raw/station_ops_snapshot.csv', header = true);
