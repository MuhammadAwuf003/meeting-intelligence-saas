"""
Transcript parser: handles TXT and PDF uploads, extracts and cleans text.
"""

import re
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode raw bytes from a TXT upload."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_bytes.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue
    raise ValueError("Unable to decode text file with supported encodings.")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file using PyPDF2."""
    try:
        import PyPDF2  # type: ignore

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        raise ValueError(f"Could not extract text from PDF: {exc}") from exc


def clean_transcript(raw_text: str) -> str:
    """
    Normalize and clean a raw transcript string.

    Steps:
    - Collapse multiple blank lines into one
    - Strip leading/trailing whitespace per line
    - Remove non-printable characters
    - Normalize smart quotes and dashes
    """
    # Remove non-printable control characters (except newlines/tabs)
    text = re.sub(r"[^\S\n\t ]+", " ", raw_text)

    # Normalize smart quotes and dashes
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)

    # Strip each line
    lines = [line.strip() for line in text.splitlines()]

    # Collapse consecutive blank lines
    cleaned_lines: list[str] = []
    blank_streak = 0
    for line in lines:
        if line == "":
            blank_streak += 1
            if blank_streak <= 1:
                cleaned_lines.append("")
        else:
            blank_streak = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def parse_transcript(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline: extract → clean → compute basic stats.

    Returns a dict with keys:
        raw_text      – original extracted text
        clean_text    – cleaned text
        word_count    – approximate word count
        line_count    – number of non-empty lines
        speakers      – list of unique detected speaker labels
        speaker_count – number of unique speakers
    """
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext == "txt":
        raw_text = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    clean_text = clean_transcript(raw_text)
    word_count = len(clean_text.split())
    non_empty_lines = [l for l in clean_text.splitlines() if l.strip()]

    # Detect speaker labels like "John:", "ALICE:", "[Bob]:"
    speaker_pattern = re.compile(
        r"^(?:\[)?([A-Z][a-zA-Z\s\-']{1,30})(?:\])?\s*:", re.MULTILINE
    )
    speakers = list({m.group(1).strip() for m in speaker_pattern.finditer(clean_text)})

    return {
        "raw_text": raw_text,
        "clean_text": clean_text,
        "word_count": word_count,
        "line_count": len(non_empty_lines),
        "speakers": speakers,
        "speaker_count": len(speakers),
    }
