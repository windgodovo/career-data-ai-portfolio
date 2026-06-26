# Runbook: Excel to AI Auto-Report Agent

## 1. Setup

1. Create virtual environment.
2. Install dependencies.
3. Copy .env.example to .env and fill config.

Example:

```bash
cd "/Volumes/new/vibe code/work finding/new work/03-excel-ai-auto-report-agent"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
```

Note:
- `cp -n` will not overwrite an existing `.env`.
- If `.env` already has your real SMTP or API settings, do not run plain `cp .env.example .env`.
- Recommended: keep real secrets in `.env.local`, because `.env.local` overrides `.env`.

Create local secret file:

```bash
cp -n .env.local.example .env.local
```

Important:
- `.env.local` with placeholder values is ignored by the app.
- Set real SMTP values in `.env.local` (recommended) or `.env`.

LLM provider notes:
- For Zhipu, set OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
- Example model: OPENAI_MODEL=glm-4.6v
- Put your own API key into OPENAI_API_KEY
- If provider does not support `/responses`, the app now auto-falls back to `chat.completions`.

Keychain mode (recommended on macOS):
- Save key once:
	security add-generic-password -a openai_api_key -s ai-auto-report -w 'your_real_key' -U
- In .env set:
	OPENAI_API_KEY=
	OPENAI_API_KEYCHAIN_SERVICE=ai-auto-report
	OPENAI_API_KEYCHAIN_ACCOUNT=openai_api_key
- The app will load OPENAI_API_KEY from Keychain when OPENAI_API_KEY is empty.

SMTP password in Keychain (recommended):
- Save SMTP auth code once:
	security add-generic-password -a smtp_password -s ai-auto-report -w 'your_qq_smtp_auth_code' -U
- In .env or .env.local set:
	SMTP_PASSWORD=
	SMTP_PASSWORD_KEYCHAIN_SERVICE=ai-auto-report
	SMTP_PASSWORD_KEYCHAIN_ACCOUNT=smtp_password
- The app will load SMTP_PASSWORD from Keychain when SMTP_PASSWORD is empty.

## 2. Input Template

Required columns:
- date
- region
- sales_amount
- cost_amount
- order_count

Supported formats:
- .csv
- .xlsx

## 3. Run Pipeline

```bash
python main.py --input data/input/sample_sales.csv --no-email
```

Without --no-email, the pipeline tries SMTP send.

## 4. Outputs

Generated into data/output:
- metrics_*.csv
- invalid_rows_*.csv
- ai_summary_*.txt
- payload_*.json
- report_summary_*.pdf (if reportlab is installed)

Email output:
- HTML formatted email body for better readability on mobile.
- Output files are attached to the email automatically.

## 5. Scheduler

Use cron.example to configure daily run.

```bash
bash scheduler/run_daily.sh
```

## 6. Troubleshooting

- Missing columns: check template header names.
- SMTP send skipped: check .env values.
- OpenAI key missing: fallback summary is used.
- socket.gaierror nodename nor servname: SMTP_HOST is invalid or DNS unavailable.
- SMTPAuthenticationError: use QQ SMTP authorization code, not QQ account password.
