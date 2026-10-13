
"""
Project : Document Converter
Project ID : 034

Document Conversion Service
"""

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.table import Table as DocxTable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph as PdfParagraph,
    SimpleDocTemplate,
    Spacer,
    Table as PdfTable,
    TableStyle,
)

from src.config import (
    DEFAULT_OUTPUT_EXTENSION,
    OVERWRITE_OUTPUT_FILES,
    PDF_SIGNATURE,
    SUPPORTED_INPUT_EXTENSIONS,
)


@dataclass(frozen=True)
class ConversionResult:
    """Represent the outcome of a document conversion."""

    success: bool
    input_path: str
    output_path: str
    message: str
    error_details: str | None = None


class DocumentConversionService:
    """Convert DOCX documents to PDF using Python."""

    def convert_docx_to_pdf(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
    ) -> ConversionResult:
        """Convert a DOCX file to PDF and validate the output."""

        source = Path(input_path).expanduser().resolve()
        destination = (
            source.with_suffix(DEFAULT_OUTPUT_EXTENSION)
            if output_path is None
            else Path(output_path).expanduser().resolve()
        )

        validation_error = self._validate_paths(
            source, destination
        )

        if validation_error:
            return self._failure(
                source,
                destination,
                "Conversion validation failed.",
                validation_error,
            )

        try:
            document = Document(str(source))
            destination.parent.mkdir(
                parents=True, exist_ok=True
            )

            with tempfile.TemporaryDirectory(
                prefix="document_converter_"
            ) as temporary_directory:
                temporary_pdf = (
                    Path(temporary_directory) / destination.name
                )

                pdf_document = SimpleDocTemplate(
                    str(temporary_pdf),
                    pagesize=A4,
                    rightMargin=20 * mm,
                    leftMargin=20 * mm,
                    topMargin=20 * mm,
                    bottomMargin=20 * mm,
                    title=source.stem,
                    author="Document Converter",
                )

                pdf_document.build(
                    self._build_pdf_content(document)
                )

                if not self._is_valid_pdf(temporary_pdf):
                    return self._failure(
                        source,
                        destination,
                        "Generated PDF failed validation.",
                        "The temporary PDF is empty or has "
                        "an invalid signature.",
                    )

                if (
                    destination.exists()
                    and not OVERWRITE_OUTPUT_FILES
                ):
                    return self._failure(
                        source,
                        destination,
                        "Output file already exists.",
                        "The existing output was preserved. "
                        "Choose another path.",
                    )

                shutil.move(
                    str(temporary_pdf),
                    str(destination),
                )

            if not self._is_valid_pdf(destination):
                return self._failure(
                    source,
                    destination,
                    "Final output PDF failed validation.",
                    "The saved output is empty or has "
                    "an invalid signature.",
                )

            return ConversionResult(
                success=True,
                input_path=str(source),
                output_path=str(destination),
                message=(
                    "DOCX to PDF conversion completed successfully. "
                    "Basic paragraph formatting and tables were applied."
                ),
            )

        except Exception as error:
            return self._failure(
                source,
                destination,
                "Document conversion failed.",
                f"{type(error).__name__}: {error}",
            )

    @classmethod
    def _build_pdf_content(
        cls,
        document: DocumentObject,
    ) -> list:
        """Translate paragraphs and tables in document order."""

        styles = getSampleStyleSheet()

        styles.add(
            ParagraphStyle(
                name="DocumentBody",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                spaceAfter=6,
                alignment=TA_LEFT,
                textColor=colors.black,
            )
        )

        styles.add(
            ParagraphStyle(
                name="DocumentTitle",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=25,
                spaceAfter=14,
                alignment=TA_CENTER,
            )
        )

        styles.add(
            ParagraphStyle(
                name="DocumentTableCell",
                parent=styles["BodyText"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                spaceAfter=2,
                alignment=TA_LEFT,
                wordWrap="LTR",
            )
        )

        for level, size, leading in (
            (1, 16, 20),
            (2, 13, 17),
            (3, 11, 14),
        ):
            styles.add(
                ParagraphStyle(
                    name=f"DocumentHeading{level}",
                    parent=styles[f"Heading{level}"],
                    fontName="Helvetica-Bold",
                    fontSize=size,
                    leading=leading,
                    spaceBefore=8,
                    spaceAfter=6,
                )
            )

        story = []

        # Iterate over the Word document body to preserve the
        # original order of paragraphs and tables.
        for element in document.element.body.iterchildren():
            if isinstance(element, CT_P):
                paragraph = DocxParagraph(element, document)

                if paragraph.paragraph_format.page_break_before:
                    story.append(PageBreak())

                text = cls._format_paragraph_runs(paragraph)

                if not text.strip():
                    story.append(Spacer(1, 4))
                    continue

                style_name = cls._get_pdf_style(
                    paragraph.style.name
                )
                story.append(
                    PdfParagraph(text, styles[style_name])
                )

            elif isinstance(element, CT_Tbl):
                docx_table = DocxTable(element, document)
                pdf_table = cls._build_pdf_table(
                    docx_table, styles
                )

                if pdf_table is not None:
                    story.append(Spacer(1, 4))
                    story.append(pdf_table)
                    story.append(Spacer(1, 8))

        if not story:
            story.append(
                PdfParagraph(
                    "The source document contains no paragraphs or tables.",
                    styles["DocumentBody"],
                )
            )

        return story

    @classmethod
    def _build_pdf_table(
        cls,
        docx_table: DocxTable,
        styles,
    ) -> PdfTable | None:
        """Convert a Word table into a ReportLab table."""

        rows = []

        for row in docx_table.rows:
            cells = []

            for cell in row.cells:
                paragraphs = []

                for paragraph in cell.paragraphs:
                    text = cls._format_paragraph_runs(paragraph)

                    if text.strip():
                        paragraphs.append(
                            PdfParagraph(
                                text,
                                styles["DocumentTableCell"],
                            )
                        )

                if not paragraphs:
                    paragraphs.append(
                        PdfParagraph(
                            " ",
                            styles["DocumentTableCell"],
                        )
                    )

                cells.append(paragraphs)

            if cells:
                rows.append(cells)

        if not rows:
            return None

        column_count = max(len(row) for row in rows)

        # Normalize rows if the source contains irregular row widths.
        for row in rows:
            while len(row) < column_count:
                row.append(
                    [
                        PdfParagraph(
                            " ",
                            styles["DocumentTableCell"],
                        )
                    ]
                )

        available_width = A4[0] - (40 * mm)
        column_width = available_width / column_count

        table = PdfTable(
            rows,
            colWidths=[column_width] * column_count,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )

        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _format_paragraph_runs(
        paragraph: DocxParagraph,
    ) -> str:
        """Escape text and preserve basic bold and italic formatting."""

        formatted_runs = []

        for run in paragraph.runs:
            text = escape(run.text).replace("\n", "<br/>")

            if not text:
                continue

            if run.bold and run.italic:
                text = f"<b><i>{text}</i></b>"
            elif run.bold:
                text = f"<b>{text}</b>"
            elif run.italic:
                text = f"<i>{text}</i>"

            formatted_runs.append(text)

        if formatted_runs:
            return "".join(formatted_runs)

        return escape(paragraph.text).replace("\n", "<br/>")

    @staticmethod
    def _get_pdf_style(style_name: str) -> str:
        """Map common Word paragraph styles to PDF styles."""

        normalized = style_name.strip().lower()

        if normalized == "title":
            return "DocumentTitle"

        for level in (1, 2, 3):
            if normalized.startswith(f"heading {level}"):
                return f"DocumentHeading{level}"

        return "DocumentBody"

    @staticmethod
    def _validate_paths(
        source: Path,
        destination: Path,
    ) -> str | None:
        """Validate input and output paths before conversion."""

        if not source.exists():
            return f"Input file does not exist: {source}"

        if not source.is_file():
            return f"Input path is not a file: {source}"

        if source.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
            return (
                "Unsupported input format. Supported formats: "
                + ", ".join(SUPPORTED_INPUT_EXTENSIONS)
            )

        if source.stat().st_size == 0:
            return "Input document is empty."

        if destination.suffix.lower() != DEFAULT_OUTPUT_EXTENSION:
            return f"Output file must use {DEFAULT_OUTPUT_EXTENSION}."

        if source == destination:
            return "Input and output paths must be different."

        if destination.exists() and not OVERWRITE_OUTPUT_FILES:
            return f"Output file already exists: {destination}"

        return None

    @staticmethod
    def _is_valid_pdf(pdf_path: Path) -> bool:
        """Check that the PDF exists, is non-empty, and has a PDF signature."""

        try:
            if (
                not pdf_path.is_file()
                or pdf_path.stat().st_size == 0
            ):
                return False

            with pdf_path.open("rb") as pdf_file:
                return (
                    pdf_file.read(len(PDF_SIGNATURE))
                    == PDF_SIGNATURE
                )

        except OSError:
            return False

    @staticmethod
    def _failure(
        source: Path,
        destination: Path,
        message: str,
        details: str,
    ) -> ConversionResult:
        """Build a consistent conversion failure result."""

        return ConversionResult(
            success=False,
            input_path=str(source),
            output_path=str(destination),
            message=message,
            error_details=details,
        )


# Public Interface
#
# Public class:
#   DocumentConversionService
#
# Public data model:
#   ConversionResult
#
# Public methods:
#   convert_docx_to_pdf(input_path, output_path=None)
#
# Dependencies:
#   Python standard library, python-docx, reportlab, src.config
#
# External applications:
#   None required
