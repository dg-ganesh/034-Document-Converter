
"""
Project : Document Converter
Project ID : 034

Execution Report Service
"""

from datetime import datetime
from pathlib import Path
from time import perf_counter

from src.config import (
    APP_VERSION,
    EXECUTION_REPORT_PATH,
    PROJECT_NAME,
)


class ExecutionReportService:
    """Create and maintain the application execution report."""

    def __init__(self, report_path: Path = EXECUTION_REPORT_PATH) -> None:
        self.report_path = Path(report_path)
        self.started_at: datetime | None = None
        self.started_counter: float | None = None
        self.last_successful_checkpoint = "None"
        self._checkpoints: list[tuple[str, str, str]] = []
        self._errors: list[str] = []

    def start_report(self) -> None:
        """Initialize a new report for the current application run."""
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

        self.started_at = datetime.now()
        self.started_counter = perf_counter()
        self.last_successful_checkpoint = "None"
        self._checkpoints.clear()
        self._errors.clear()

        header = [
            f"Project: {PROJECT_NAME}",
            f"Application Version: {APP_VERSION}",
            f"Execution Start Time: "
            f"{self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "Overall Status: IN PROGRESS",
            "",
            "Execution Checkpoints:",
        ]

        self.report_path.write_text(
            "\n".join(header) + "\n",
            encoding="utf-8",
        )

    def record_checkpoint(
        self,
        checkpoint: str,
        status: str,
        details: str = "",
    ) -> None:
        """Record a named checkpoint with its outcome and optional details."""
        self._ensure_started()

        normalized_status = status.strip().upper()

        if normalized_status not in {"PASS", "FAIL", "SKIP"}:
            raise ValueError(
                "Checkpoint status must be PASS, FAIL, or SKIP."
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._checkpoints.append(
            (checkpoint, normalized_status, details)
        )

        if normalized_status == "PASS":
            self.last_successful_checkpoint = checkpoint

        if normalized_status == "FAIL" and details:
            self.record_error(details, write_report=False)

        self._rewrite_report()

    def record_error(
        self,
        error: str,
        write_report: bool = True,
    ) -> None:
        """Record an error message for diagnosis."""
        self._ensure_started()
        self._errors.append(str(error))

        if write_report:
            self._rewrite_report()

    def finalize_report(self, overall_status: str | None = None) -> None:
        """Finalize the report and record its duration and final status."""
        self._ensure_started()

        if overall_status is None:
            overall_status = (
                "FAIL"
                if any(status == "FAIL" for _, status, _ in self._checkpoints)
                else "PASS"
            )

        overall_status = overall_status.strip().upper()

        if overall_status not in {"PASS", "FAIL"}:
            raise ValueError("Overall status must be PASS or FAIL.")

        self._rewrite_report(final_status=overall_status)

    def _ensure_started(self) -> None:
        if self.started_at is None or self.started_counter is None:
            raise RuntimeError(
                "Start the execution report before recording results."
            )

    def _rewrite_report(self, final_status: str | None = None) -> None:
        """Rewrite the report with all currently recorded information."""
        self._ensure_started()

        elapsed = perf_counter() - self.started_counter
        now = datetime.now()

        if final_status is None:
            final_status = "IN PROGRESS"

        lines = [
            f"Project: {PROJECT_NAME}",
            f"Application Version: {APP_VERSION}",
            f"Execution Start Time: "
            f"{self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {final_status}",
            f"Execution Duration: {elapsed:.2f} seconds",
            f"Last Successful Checkpoint: "
            f"{self.last_successful_checkpoint}",
            "",
            "Execution Checkpoints:",
        ]

        if self._checkpoints:
            for checkpoint, status, details in self._checkpoints:
                line = f"[{status}] {checkpoint}"
                if details:
                    line += f" - {details}"
                lines.append(line)
        else:
            lines.append("No checkpoints recorded.")

        lines.extend(["", "Errors:"])

        if self._errors:
            lines.extend(f"- {error}" for error in self._errors)
        else:
            lines.append("None")

        self.report_path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Public Interface
# ---------------------------------------------------------------------------
#
# Public class:
#   ExecutionReportService
#
# Public methods:
#   start_report()
#   record_checkpoint(checkpoint, status, details="")
#   record_error(error, write_report=True)
#   finalize_report(overall_status=None)
#
# Dependencies:
#   pathlib, datetime, time (Python standard library)
#   src.config
