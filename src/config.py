
"""
Project : Document Converter
Project ID : 034

Application Configuration
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Project Identity
# ---------------------------------------------------------------------------

PROJECT_NAME = "Document Converter"
PROJECT_ID = "034"
APP_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SRC_DIR = PROJECT_ROOT / "src"
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
LOGS_DIR = PROJECT_ROOT / "logs"
TESTS_DIR = PROJECT_ROOT / "tests"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
RELEASES_DIR = PROJECT_ROOT / "releases"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"


# ---------------------------------------------------------------------------
# Asset Paths
# ---------------------------------------------------------------------------

ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"


# ---------------------------------------------------------------------------
# Data Paths
# ---------------------------------------------------------------------------

INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
SAMPLES_DIR = DATA_DIR / "samples"


# ---------------------------------------------------------------------------
# Runtime Artifacts
# ---------------------------------------------------------------------------

EXECUTION_REPORT_PATH = LOGS_DIR / "execution_report.txt"
APPLICATION_LOG_PATH = LOGS_DIR / "application.log"
DEBUG_LOG_PATH = LOGS_DIR / "debug.log"


# ---------------------------------------------------------------------------
# Document Conversion Configuration
# ---------------------------------------------------------------------------

SUPPORTED_INPUT_EXTENSIONS = (".docx",)
SUPPORTED_OUTPUT_EXTENSIONS = (".pdf",)

DEFAULT_OUTPUT_EXTENSION = ".pdf"

# LibreOffice will be detected by the environment service.
# Its executable path is not assumed or hardcoded here.


# ---------------------------------------------------------------------------
# Application Defaults
# ---------------------------------------------------------------------------

DEFAULT_ENCODING = "utf-8"
PDF_SIGNATURE = b"%PDF-"

OVERWRITE_OUTPUT_FILES = False


# ---------------------------------------------------------------------------
# Public Interface
# ---------------------------------------------------------------------------
#
# Public constants:
#   PROJECT_NAME
#   PROJECT_ID
#   APP_VERSION
#   PROJECT_ROOT
#   LOGS_DIR
#   INPUT_DIR
#   OUTPUT_DIR
#   SAMPLES_DIR
#   EXECUTION_REPORT_PATH
#   SUPPORTED_INPUT_EXTENSIONS
#   SUPPORTED_OUTPUT_EXTENSIONS
#   DEFAULT_OUTPUT_EXTENSION
#   DEFAULT_ENCODING
#   PDF_SIGNATURE
#   OVERWRITE_OUTPUT_FILES
#
# Public methods:
#   None
#
# Public signals:
#   None
#
# Dependencies:
#   pathlib.Path (Python standard library)
