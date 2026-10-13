
"""
Project : Document Converter
Project ID : 034

Application Entry Point
"""

import sys
import tkinter as tk
from pathlib import Path

from src.config import APP_VERSION, PROJECT_NAME
from src.services.environment_service import EnvironmentService
from src.services.execution_report_service import (
    ExecutionReportService,
)
from src.ui.main_window import MainWindow


def main() -> int:
    """Validate the environment, launch the UI, and report execution."""

    report = ExecutionReportService()
    exit_code = 0

    report.start_report()

    try:
        report.record_checkpoint(
            "Application Bootstrap",
            "PASS",
            f"{PROJECT_NAME} v{APP_VERSION} started.",
        )

        print(f"{PROJECT_NAME} v{APP_VERSION}")
        print("Validating application environment...")

        environment_results = (
            EnvironmentService().validate_environment()
        )

        for result in environment_results:
            report.record_checkpoint(
                result.name,
                result.status,
                result.details,
            )
            print(
                f"[{result.status}] "
                f"{result.name}: {result.details}"
            )

        failed_checks = [
            result
            for result in environment_results
            if result.status != "PASS"
        ]

        if failed_checks:
            report.record_checkpoint(
                "Environment Validation",
                "FAIL",
                f"{len(failed_checks)} environment check(s) failed.",
            )
            exit_code = 1
            return exit_code

        report.record_checkpoint(
            "Environment Validation",
            "PASS",
            "All environment checks passed.",
        )

        report.record_checkpoint(
            "Desktop UI Initialization",
            "PASS",
            "Creating the Tkinter main window.",
        )

        root = tk.Tk()
        MainWindow(root).run()

        report.record_checkpoint(
            "Desktop UI Shutdown",
            "PASS",
            "The desktop application closed normally.",
        )

    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        report.record_checkpoint(
            "Application Execution",
            "SKIP",
            "Application interrupted by user.",
        )

    except Exception as exc:
        exit_code = 1
        details = f"{type(exc).__name__}: {exc}"

        report.record_checkpoint(
            "Application Execution",
            "FAIL",
            details,
        )
        report.record_error(
            details,
            write_report=False,
        )

        print(f"\n[FAIL] Application error: {details}")

    finally:
        report.finalize_report(
            "FAIL" if exit_code != 0 else None
        )

        report_path = Path(
            "logs/execution_report.txt"
        ).resolve()

        print(f"\nExecution report: {report_path}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())


# Public interface
# Function: main()
# Responsibilities: Environment validation, desktop UI startup,
#   application shutdown and execution reporting.
# Dependencies: Tkinter and existing project services.
