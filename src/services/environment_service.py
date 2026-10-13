
"""
Project : Document Converter
Project ID : 034

Environment Validation Service
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from src.config import (
    DATA_DIR,
    INPUT_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    PROJECT_ROOT,
    SAMPLES_DIR,
    SRC_DIR,
)


@dataclass(frozen=True)
class EnvironmentCheckResult:
    """Represent the outcome of a single environment check."""

    name: str
    status: str
    details: str
    resolved_path: str | None = None


class EnvironmentService:
    """Validate the Python runtime and application directories."""

    MINIMUM_PYTHON_VERSION = (3, 14)

    def validate_environment(self) -> list[EnvironmentCheckResult]:
        """Run all environment checks and return their results."""
        results: list[EnvironmentCheckResult] = []

        results.append(self._check_python_version())
        results.append(self._check_project_structure())
        results.extend(self._prepare_runtime_directories())

        return results

    def _check_python_version(self) -> EnvironmentCheckResult:
        """Verify that the active Python version meets requirements."""
        current_version = sys.version_info[:2]
        current_text = f"{current_version[0]}.{current_version[1]}"
        minimum_text = (
            f"{self.MINIMUM_PYTHON_VERSION[0]}."
            f"{self.MINIMUM_PYTHON_VERSION[1]}"
        )

        if current_version >= self.MINIMUM_PYTHON_VERSION:
            return EnvironmentCheckResult(
                name="Python Version",
                status="PASS",
                details=f"Python {current_text} detected.",
                resolved_path=sys.executable,
            )

        return EnvironmentCheckResult(
            name="Python Version",
            status="FAIL",
            details=(
                f"Python {minimum_text} or later is required. "
                f"Detected Python {current_text}."
            ),
            resolved_path=sys.executable,
        )

    def _check_project_structure(self) -> EnvironmentCheckResult:
        """Verify that the project root and source directory exist."""
        required_directories = (PROJECT_ROOT, SRC_DIR)

        missing_directories = [
            str(directory)
            for directory in required_directories
            if not directory.is_dir()
        ]

        if missing_directories:
            return EnvironmentCheckResult(
                name="Project Structure",
                status="FAIL",
                details=(
                    "Required project directories are missing: "
                    + ", ".join(missing_directories)
                ),
            )

        return EnvironmentCheckResult(
            name="Project Structure",
            status="PASS",
            details="Project root and source directory are available.",
            resolved_path=str(PROJECT_ROOT),
        )

    def _prepare_runtime_directories(
        self,
    ) -> list[EnvironmentCheckResult]:
        """Create standard runtime directories when necessary."""
        directories = (
            DATA_DIR,
            INPUT_DIR,
            OUTPUT_DIR,
            SAMPLES_DIR,
            LOGS_DIR,
        )

        results: list[EnvironmentCheckResult] = []

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)

                if not directory.is_dir():
                    raise OSError(
                        "Path exists but is not a directory."
                    )

                results.append(
                    EnvironmentCheckResult(
                        name=f"Directory: {directory.name}",
                        status="PASS",
                        details="Directory is available.",
                        resolved_path=str(directory),
                    )
                )

            except OSError as error:
                results.append(
                    EnvironmentCheckResult(
                        name=f"Directory: {directory.name}",
                        status="FAIL",
                        details=str(error),
                        resolved_path=str(directory),
                    )
                )

        return results


# ---------------------------------------------------------------------------
# Public Interface
# ---------------------------------------------------------------------------
#
# Public class:
#   EnvironmentService
#
# Public data model:
#   EnvironmentCheckResult
#
# Public methods:
#   validate_environment()
#
# Dependencies:
#   sys, dataclasses, pathlib (Python standard library)
#   src.config
#
# External applications:
#   None required
