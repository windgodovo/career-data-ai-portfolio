from __future__ import annotations

import sqlite3
from pathlib import Path


class AuditStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_table()

    def _init_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qa_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    rewritten_question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    citation_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def add_row(
        self,
        request_id: str,
        question: str,
        rewritten_question: str,
        answer: str,
        confidence: float,
        latency_ms: int,
        citation_count: int,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO qa_audit (
                    request_id, question, rewritten_question, answer,
                    confidence, latency_ms, citation_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    question,
                    rewritten_question,
                    answer,
                    confidence,
                    latency_ms,
                    citation_count,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def metrics(self) -> tuple[int, float, float]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(AVG(latency_ms), 0),
                    COALESCE(AVG(confidence), 0)
                FROM qa_audit
                """
            ).fetchone()
            if row is None:
                return (0, 0.0, 0.0)
            return (int(row[0]), float(row[1]), float(row[2]))
        finally:
            conn.close()
