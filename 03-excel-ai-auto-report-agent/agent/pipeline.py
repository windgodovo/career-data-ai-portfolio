from __future__ import annotations

import argparse
import html
from pathlib import Path

from .config import ROOT_DIR, load_settings
from .email_sender import send_email
from .io_loader import load_tabular_file
from .metrics import build_kpis, make_anomaly_hints
from .report_writer import write_outputs
from .summarizer import generate_ai_summary
from .validate import validate_frame


def _build_email_bodies(
        input_path: Path,
        valid_rows: int,
        invalid_rows: int,
        output_paths: dict,
        ai_summary: str,
) -> tuple[str, str]:
        output_lines = [f"- {k}: {v}" for k, v in output_paths.items()]
        text_body = (
                "Pipeline finished successfully.\n\n"
                f"Input: {input_path}\n"
                f"Valid rows: {valid_rows}\n"
                f"Invalid rows: {invalid_rows}\n\n"
                "Output files:\n"
                + "\n".join(output_lines)
                + "\n\nAI Summary:\n"
                + ai_summary
                + "\n"
        )

        html_summary = "<br>".join(html.escape(ai_summary).splitlines())
        html_outputs = "".join(
                f"<li><b>{html.escape(k)}</b>: {html.escape(str(v))}</li>" for k, v in output_paths.items()
        )
        html_body = f"""
<html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.55; color: #1f2937;">
        <h2 style="margin-bottom: 8px;">Daily Excel AI Report</h2>
        <p style="margin-top: 0; color: #4b5563;">Pipeline finished successfully.</p>
        <table style="border-collapse: collapse; width: 100%; max-width: 680px;">
            <tr><td style="padding: 6px 0; width: 140px;"><b>Input</b></td><td>{html.escape(str(input_path))}</td></tr>
            <tr><td style="padding: 6px 0;"><b>Valid rows</b></td><td>{valid_rows}</td></tr>
            <tr><td style="padding: 6px 0;"><b>Invalid rows</b></td><td>{invalid_rows}</td></tr>
        </table>
        <h3 style="margin-top: 20px; margin-bottom: 8px;">Output Files</h3>
        <ul style="margin-top: 0;">{html_outputs}</ul>
        <h3 style="margin-top: 20px; margin-bottom: 8px;">AI Summary</h3>
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px;">{html_summary}</div>
    </body>
</html>
""".strip()
        return text_body, html_body


def run_pipeline() -> None:
    parser = argparse.ArgumentParser(
        description="Excel to AI Auto-Report Agent pipeline"
    )
    parser.add_argument(
        "--input",
        default=str(ROOT_DIR / "data" / "input" / "sample_sales.csv"),
        help="Path to input .csv/.xlsx file",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT_DIR / "data" / "output"),
        help="Directory for output files",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email even if SMTP is configured",
    )
    args = parser.parse_args()

    settings = load_settings()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = load_tabular_file(input_path)
    validation = validate_frame(df)
    kpis = build_kpis(validation.clean_df)
    hints = make_anomaly_hints(kpis["by_region"])

    summary_payload = {
        "summary": kpis["summary"],
        "hints": hints,
        "invalid_rows": int(len(validation.invalid_df)),
    }
    ai_summary = generate_ai_summary(settings, summary_payload)

    output_paths = write_outputs(
        output_dir=output_dir,
        kpis=kpis,
        invalid_df=validation.invalid_df,
        ai_summary=ai_summary,
    )

    email_subject = "Daily Excel AI Report"
    email_body, email_html = _build_email_bodies(
        input_path=input_path,
        valid_rows=len(validation.clean_df),
        invalid_rows=len(validation.invalid_df),
        output_paths=output_paths,
        ai_summary=ai_summary,
    )

    if not args.no_email:
        send_email(
            settings,
            email_subject,
            email_body,
            html_body=email_html,
            attachments=list(output_paths.values()),
        )

    print(email_body)
