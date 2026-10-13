
"""
Project : Document Converter
Project ID : 034

Batch Conversion Service
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.services.document_conversion_service import (
    DocumentConversionService,
)
from src.services.pdf_to_docx_service import PDFToDOCXService
from src.services.text_conversion_service import (
    TextConversionService,
)


ProgressCallback = Callable[[int, int, str], None]


@dataclass(frozen=True)
class BatchFileResult:
    """Result of processing one file in a batch."""

    success: bool
    operation: str
    input_path: str
    output_path: str
    message: str
    error_details: str = ""


@dataclass(frozen=True)
class BatchConversionResult:
    """Summary of a completed batch."""

    total_files: int
    successful_files: int
    failed_files: int
    results: tuple[BatchFileResult, ...]

    @property
    def success(self) -> bool:
        """Return true when every file was processed successfully."""

        return self.total_files > 0 and self.failed_files == 0

    @property
    def completed_files(self) -> int:
        """Return the number of files that reached a result."""

        return self.successful_files + self.failed_files


class BatchConversionService:
    """Coordinate supported conversions for multiple files."""

    SUPPORTED_OPERATIONS = {
        "docx_to_pdf",
        "pdf_to_docx",
        "docx_to_txt",
        "txt_to_docx",
    }

    def __init__(self) -> None:
        self._docx_pdf_service = DocumentConversionService()
        self._pdf_docx_service = PDFToDOCXService()
        self._text_service = TextConversionService()

    def process_batch(
        self,
        input_paths: list[str | Path],
        operation: str,
        output_directory: str | Path,
        progress_callback: ProgressCallback | None = None,
    ) -> BatchConversionResult:
        """
        Process files sequentially and return per-file results.

        Supported operation names:
        docx_to_pdf, pdf_to_docx, docx_to_txt, txt_to_docx.

        PDF merge and page extraction are intentionally excluded
        from this per-file batch interface because they require
        multiple inputs or a page-selection parameter.
        """

        if operation not in self.SUPPORTED_OPERATIONS:
            raise ValueError(
                f"Unsupported batch operation: {operation}"
            )

        sources = [
            Path(path).expanduser().resolve()
            for path in input_paths
        ]
        destination_directory = (
            Path(output_directory).expanduser().resolve()
        )

        if not sources:
            raise ValueError(
                "Select at least one input file."
            )

        if not destination_directory.exists():
            destination_directory.mkdir(
                parents=True, exist_ok=True
            )

        if not destination_directory.is_dir():
            raise ValueError(
                "The output location must be a directory."
            )

        results: list[BatchFileResult] = []
        total = len(sources)

        for index, source in enumerate(sources, start=1):
            destination = (
                destination_directory
                / f"{source.stem}{self._output_extension(operation)}"
            )

            if progress_callback is not None:
                try:
                    progress_callback(
                        index - 1,
                        total,
                        source.name,
                    )
                except Exception:
                    # Progress reporting must not interrupt conversion.
                    pass

            result = self._process_one(
                source,
                destination,
                operation,
            )
            results.append(result)

            if progress_callback is not None:
                try:
                    progress_callback(
                        index,
                        total,
                        source.name,
                    )
                except Exception:
                    # Progress reporting must not interrupt conversion.
                    pass

        successful = sum(
            1 for result in results if result.success
        )
        failed = total - successful

        return BatchConversionResult(
            total_files=total,
            successful_files=successful,
            failed_files=failed,
            results=tuple(results),
        )

    def _process_one(
        self,
        source: Path,
        destination: Path,
        operation: str,
    ) -> BatchFileResult:
        """Process one file without stopping the remaining batch."""

        try:
            if not source.exists():
                return self._failure(
                    operation,
                    source,
                    destination,
                    "Input file does not exist.",
                )

            if not source.is_file():
                return self._failure(
                    operation,
                    source,
                    destination,
                    "Input path is not a file.",
                )

            expected_extension = self._input_extension(operation)
            if source.suffix.lower() != expected_extension:
                return self._failure(
                    operation,
                    source,
                    destination,
                    f"Expected a {expected_extension} input file.",
                )

            if destination.exists():
                return self._failure(
                    operation,
                    source,
                    destination,
                    "Output file already exists; it was not overwritten.",
                )

            if operation == "docx_to_pdf":
                result = (
                    self._docx_pdf_service.convert_docx_to_pdf(
                        source, destination
                    )
                )
            elif operation == "pdf_to_docx":
                result = (
                    self._pdf_docx_service.convert_pdf_to_docx(
                        source, destination
                    )
                )
            elif operation == "docx_to_txt":
                result = self._text_service.convert_docx_to_txt(
                    source, destination
                )
            else:
                result = self._text_service.convert_txt_to_docx(
                    source, destination
                )

            return BatchFileResult(
                success=result.success,
                operation=operation,
                input_path=str(source),
                output_path=str(destination),
                message=result.message,
                error_details=result.error_details,
            )

        except Exception as exc:
            return self._failure(
                operation,
                source,
                destination,
                f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _input_extension(operation: str) -> str:
        """Return the required source extension."""

        return {
            "docx_to_pdf": ".docx",
            "pdf_to_docx": ".pdf",
            "docx_to_txt": ".docx",
            "txt_to_docx": ".txt",
        }[operation]

    @staticmethod
    def _output_extension(operation: str) -> str:
        """Return the output extension."""

        return {
            "docx_to_pdf": ".pdf",
            "pdf_to_docx": ".docx",
            "docx_to_txt": ".txt",
            "txt_to_docx": ".docx",
        }[operation]

    @staticmethod
    def _failure(
        operation: str,
        source: Path,
        destination: Path,
        error_details: str,
    ) -> BatchFileResult:
        """Build a consistent per-file failure result."""

        return BatchFileResult(
            success=False,
            operation=operation,
            input_path=str(source),
            output_path=str(destination),
            message="File conversion failed.",
            error_details=error_details,
        )


# Public interface
# Classes:
#   BatchConversionService
#   BatchConversionResult
#   BatchFileResult
# Method:
#   process_batch(input_paths, operation, output_directory,
#                  progress_callback=None)
# Progress callback: callback(completed_count, total_count, filename)
# Dependencies: Existing conversion services and Python standard library.
