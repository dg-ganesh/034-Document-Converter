
"""
Project : Document Converter
Project ID : 034

Conversion History Service
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

from src.config import DATA_DIR


@dataclass(frozen=True)
class ConversionHistoryRecord:
    """Represent one stored conversion attempt."""

    record_id: int
    timestamp: str
    operation: str
    input_path: str
    output_path: str
    status: str
    message: str
    error_details: str


class ConversionHistoryService:
    """Store and retrieve conversion history in a local SQLite database."""

    def __init__(
        self,
        database_path: str | Path | None = None,
    ) -> None:
        self.database_path = (
            Path(database_path).expanduser().resolve()
            if database_path is not None
            else (DATA_DIR / "conversion_history.sqlite3").resolve()
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize_database()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a database connection and always close it."""

        connection = sqlite3.connect(
            str(self.database_path),
            timeout=10,
        )
        connection.row_factory = sqlite3.Row

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        """Create the history table when it does not exist."""

        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    input_path TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    error_details TEXT NOT NULL DEFAULT ''
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_conversion_history_timestamp
                ON conversion_history (timestamp DESC)
                """
            )

    def record_conversion(
        self,
        operation: str,
        input_path: str | Path,
        output_path: str | Path,
        success: bool,
        message: str,
        error_details: str = "",
    ) -> int:
        """Store one conversion attempt and return its record ID."""

        if not operation.strip():
            raise ValueError("Operation cannot be empty.")

        if not message.strip():
            raise ValueError("Message cannot be empty.")

        timestamp = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )
        status = "PASS" if success else "FAIL"

        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO conversion_history (
                    timestamp,
                    operation,
                    input_path,
                    output_path,
                    status,
                    message,
                    error_details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    operation.strip(),
                    str(input_path),
                    str(output_path),
                    status,
                    message.strip(),
                    (error_details or "").strip(),
                ),
            )

            return int(cursor.lastrowid)

    def get_recent_records(
        self,
        limit: int = 100,
    ) -> list[ConversionHistoryRecord]:
        """Return the most recent history records."""

        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    timestamp,
                    operation,
                    input_path,
                    output_path,
                    status,
                    message,
                    error_details
                FROM conversion_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            ConversionHistoryRecord(
                record_id=row["id"],
                timestamp=row["timestamp"],
                operation=row["operation"],
                input_path=row["input_path"],
                output_path=row["output_path"],
                status=row["status"],
                message=row["message"],
                error_details=row["error_details"],
            )
            for row in rows
        ]

    def get_record_count(self) -> int:
        """Return the total number of stored conversion attempts."""

        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM conversion_history"
            ).fetchone()

        return int(row["total"])


# Public interface
# Classes:
#   ConversionHistoryService
#   ConversionHistoryRecord
# Methods:
#   record_conversion(...)
#   get_recent_records(limit=100)
#   get_record_count()
# Dependencies: Python standard library, src.config.DATA_DIR
