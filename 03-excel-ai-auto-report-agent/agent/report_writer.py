from __future__ import annotations

import json
import textwrap
from datetime import datetime
from pathlib import Path

import pandas as pd


def _write_pdf_summary(pdf_path: Path, summary: dict, ai_summary: str) -> bool:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return False

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Daily Excel AI Report")
    y -= 30

    c.setFont("Helvetica", 11)
    lines = [
        f"Total Sales: {summary['total_sales']}",
        f"Total Cost: {summary['total_cost']}",
        f"Total Profit: {summary['total_profit']}",
        f"Total Orders: {summary['total_orders']}",
        f"Profit Margin: {summary['profit_margin']}",
        "",
        "AI Summary:",
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 18

    for para in ai_summary.splitlines():
        wrapped = textwrap.wrap(para, width=95) or [""]
        for line in wrapped:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 50
            c.drawString(50, y, line)
            y -= 16

    c.save()
    return True


def write_outputs(
    output_dir: Path,
    kpis: dict,
    invalid_df: pd.DataFrame,
    ai_summary: str,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_csv = output_dir / f"metrics_{timestamp}.csv"
    invalid_csv = output_dir / f"invalid_rows_{timestamp}.csv"
    summary_txt = output_dir / f"ai_summary_{timestamp}.txt"
    payload_json = output_dir / f"payload_{timestamp}.json"
    summary_pdf = output_dir / f"report_summary_{timestamp}.pdf"

    kpis["by_region"].to_csv(metrics_csv, index=False)
    invalid_df.to_csv(invalid_csv, index=False)
    summary_txt.write_text(ai_summary, encoding="utf-8")

    serializable_payload = {
        "summary": kpis["summary"],
        "by_region": kpis["by_region"].to_dict(orient="records"),
        "by_month": kpis["by_month"].to_dict(orient="records"),
    }
    payload_json.write_text(json.dumps(serializable_payload, indent=2), encoding="utf-8")
    has_pdf = _write_pdf_summary(summary_pdf, kpis["summary"], ai_summary)

    output = {
        "metrics_csv": str(metrics_csv),
        "invalid_csv": str(invalid_csv),
        "summary_txt": str(summary_txt),
        "payload_json": str(payload_json),
    }
    if has_pdf:
        output["summary_pdf"] = str(summary_pdf)

    return output
