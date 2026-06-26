CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS dwd;
CREATE SCHEMA IF NOT EXISTS dws;
CREATE SCHEMA IF NOT EXISTS ads;
CREATE SCHEMA IF NOT EXISTS serving;
CREATE SCHEMA IF NOT EXISTS monitor;

CREATE OR REPLACE TABLE ods.customer AS
SELECT *
FROM read_csv_auto('{{ROOT}}/data/ods_raw/customer.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.account AS
SELECT *
FROM read_csv_auto('{{ROOT}}/data/ods_raw/account.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.transaction AS
SELECT *
FROM read_csv_auto('{{ROOT}}/data/ods_raw/transaction.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.credit_limit AS
SELECT *
FROM read_csv_auto('{{ROOT}}/data/ods_raw/credit_limit.csv', HEADER=TRUE);

CREATE OR REPLACE TABLE ods.overdue_record AS
SELECT *
FROM read_csv_auto('{{ROOT}}/data/ods_raw/overdue_record.csv', HEADER=TRUE);
