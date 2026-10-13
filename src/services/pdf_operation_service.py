
"""
Project : Document Converter
Project ID : 034

PDF Merge and Page Extraction Service
"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from src.config import OUTPUT_DIR


@dataclass(frozen=True)
class PDFOperationResult:
    success: bool
    input_paths: tuple[str, ...]
    output_path: str
    message: str
    error_details: str = ""


class PDFOperationService:
    """Merge PDF files and extract selected pages."""

    def merge_pdfs(
        self,
        input_paths: list[str | Path],
        output_path: str | Path,
    ) -> PDFOperationResult:
        """Merge PDFs in the order provided."""

        sources = tuple(
            Path(path).expanduser().resolve()
            for path in input_paths
        )
        destination = Path(output_path).expanduser().resolve()

        try:
            error = self._validate_inputs(
                sources, destination
            )
            if error:
                return self._failure(
                    sources, destination, error
                )

            writer = PdfWriter()

            for source in sources:
                reader = PdfReader(str(source))

                if reader.is_encrypted:
                    return self._failure(
                        sources,
                        destination,
                        f"Encrypted PDF is not supported: {source.name}",
                    )

                if not reader.pages:
                    return self._failure(
                        sources,
                        destination,
                        f"PDF contains no pages: {source.name}",
                    )

                writer.append(reader)

            self._write_output(writer, destination)

            return PDFOperationResult(
                success=True,
                input_paths=tuple(map(str, sources)),
                output_path=str(destination),
                message="PDF files merged successfully.",
            )

        except Exception as exc:
            return self._failure(
                sources,
                destination,
                f"{type(exc).__name__}: {exc}",
            )

    def extract_pages(
        self,
        input_path: str | Path,
        page_selection: str,
        output_path: str | Path | None = None,
    ) -> PDFOperationResult:
        """Extract pages using a one-based selection such as 1,3,5-7."""

        source = Path(input_path).expanduser().resolve()
        destination = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else (
                OUTPUT_DIR
                / f"{source.stem}_extracted.pdf"
            ).resolve()
        )
        sources = (source,)

        try:
            error = self._validate_inputs(
                sources, destination
            )
            if error:
                return self._failure(
                    sources, destination, error
                )

            reader = PdfReader(str(source))

            if reader.is_encrypted:
                return self._failure(
                    sources,
                    destination,
                    "Encrypted PDFs are not supported.",
                )

            page_numbers = self._parse_page_selection(
                page_selection, len(reader.pages)
            )

            writer = PdfWriter()

            for page_number in page_numbers:
                writer.add_page(reader.pages[page_number - 1])

            self._write_output(writer, destination)

            return PDFOperationResult(
                success=True,
                input_paths=(str(source),),
                output_path=str(destination),
                message=(
                    f"Extracted {len(page_numbers)} page(s) "
                    f"successfully."
                ),
            )

        except Exception as exc:
            return self._failure(
                sources,
                destination,
                f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _parse_page_selection(
        selection: str,
        total_pages: int,
    ) -> list[int]:
        """Parse one-based page numbers and inclusive ranges."""

        if not selection or not selection.strip():
            raise ValueError("Page selection cannot be empty.")

        selected: list[int] = []

        for item in selection.split(","):
            item = item.strip()

            if not item:
                raise ValueError(
                    "Page selection contains an empty item."
                )

            if "-" in item:
                parts = item.split("-")

                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid page range: {item}"
                    )

                start = int(parts[0].strip())
                end = int(parts[1].strip())

                if start > end:
                    raise ValueError(
                        f"Range start exceeds range end: {item}"
                    )

                pages = range(start, end + 1)
            else:
                pages = (int(item),)

            for page_number in pages:
                if not 1 <= page_number <= total_pages:
                    raise ValueError(
                        f"Page {page_number} is outside the "
                        f"valid range 1-{total_pages}."
                    )

                if page_number not in selected:
                    selected.append(page_number)

        if not selected:
            raise ValueError("No pages were selected.")

        return selected

    @staticmethod
    def _validate_inputs(
        sources: tuple[Path, ...],
        destination: Path,
    ) -> str | None:
        """Validate PDF input files and the output path."""

        if not sources:
            return "At least one input PDF is required."

        if destination.suffix.lower() != ".pdf":
            return "Output file must have a .pdf extension."

        if destination.exists():
            return (
                "The output file already exists. "
                "It will not be overwritten."
            )

        for source in sources:
            if not source.exists():
                return f"Input PDF does not exist: {source}"

            if not source.is_file():
                return f"Input path is not a file: {source}"

            if source.suffix.lower() != ".pdf":
                return f"Input file is not a PDF: {source}"

            if source == destination:
                return (
                    "An input PDF cannot also be the output file."
                )

        return None

    @staticmethod
    def _write_output(
        writer: PdfWriter,
        destination: Path,
    ) -> None:
        """Write the result without replacing an existing file."""

        destination.parent.mkdir(
            parents=True, exist_ok=True
        )

        # Exclusive creation prevents accidental overwrite.
        with destination.open("xb") as output_file:
            writer.write(output_file)

    @staticmethod
    def _failure(
        sources: tuple[Path, ...],
        destination: Path,
        error_details: str,
    ) -> PDFOperationResult:
        """Build a consistent failure result."""

        return PDFOperationResult(
            success=False,
            input_paths=tuple(map(str, sources)),
            output_path=str(destination),
            message="PDF operation failed.",
            error_details=error_details,
        )


# Public interface
# Class: PDFOperationService
# Methods:
#   merge_pdfs(input_paths, output_path)
#   extract_pages(input_path, page_selection, output_path=None)
# Result: PDFOperationResult
# Dependencies: pypdf, standard library, src.config.OUTPUT_DIR
