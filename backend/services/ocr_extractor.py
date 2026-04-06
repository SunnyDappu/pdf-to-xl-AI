"""
OCR Extractor Service
Handles text extraction from PDFs, supporting both:
1. Selectable text (using pdfplumber)
2. Scanned/image-based pages (using pdfplumber page.to_image + Claude Vision)

BUG FIXES:
- REMOVED pytesseract/pdf2image dependency: this PDF is fully image-based,
  pdfplumber returns empty text, and pdf2image/poppler are not installed,
  causing ALL chunks to silently fail with 0 records extracted.
- NOW uses pdfplumber's built-in page.to_image() + Claude Vision API
  to OCR image-based pages. No external system dependencies needed.
"""

import pdfplumber
import base64
import io
from typing import Tuple, Dict
import os


class OCRExtractor:
    def __init__(self, tesseract_path: str = None, anthropic_client=None):
        """
        Initialize OCR extractor.

        Args:
            tesseract_path: Ignored (kept for backwards compatibility).
            anthropic_client: An already-initialised anthropic.Anthropic()
                              client.  Pass one in so we don't need an
                              extra API key argument here.
        """
        # tesseract_path kept for API compatibility but is not used
        self._client = anthropic_client  # may be None; set later via set_client()

    def set_client(self, client):
        """Attach an Anthropic client after construction."""
        self._client = client

    # ------------------------------------------------------------------
    # Public API (unchanged signatures)
    # ------------------------------------------------------------------

    def extract_text_from_page(self, pdf_path: str, page_num: int) -> Tuple[str, str]:
        """
        Extract text from a single PDF page.

        Tries pdfplumber native text first (fast, zero-cost).
        Falls back to Claude Vision OCR for image-based pages.

        Returns:
            (extracted_text, method_used)
            method_used is one of: 'pdfplumber', 'claude_vision', 'failed'
        """
        # --- Try native text first ---
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text and len(text.strip()) > 20:
                        return text, "pdfplumber"
        except Exception:
            pass

        # --- Fall back to Claude Vision ---
        try:
            image_b64 = self._page_to_base64(pdf_path, page_num)
            if image_b64 and self._client:
                text = self._extract_via_claude_vision(image_b64)
                if text and len(text.strip()) > 0:
                    return text, "claude_vision"
        except Exception as e:
            print(f"Claude Vision OCR failed for page {page_num}: {e}")

        return "", "failed"

    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from entire PDF.

        Returns:
            (full_text, metadata_dict)
        """
        full_text = ""
        metadata = {
            "total_pages": 0,
            "pdfplumber_pages": 0,
            "claude_vision_pages": 0,
            "ocr_pages": 0,          # alias for claude_vision_pages
            "failed_pages": 0,
            "extraction_methods": {},
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)

                for page_num in range(len(pdf.pages)):
                    text, method = self.extract_text_from_page(pdf_path, page_num)

                    full_text += f"\n--- Page {page_num + 1} ({method}) ---\n"
                    full_text += text

                    if method == "pdfplumber":
                        metadata["pdfplumber_pages"] += 1
                    elif method == "claude_vision":
                        metadata["claude_vision_pages"] += 1
                        metadata["ocr_pages"] += 1
                    else:
                        metadata["failed_pages"] += 1

                    metadata["extraction_methods"][page_num + 1] = method

        except Exception as e:
            print(f"Error processing PDF: {e}")

        return full_text, metadata

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _page_to_base64(self, pdf_path: str, page_num: int) -> str:
        """Render a PDF page to a PNG and return as base64 string."""
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            # resolution=150 gives good quality without being too large
            img_obj = page.to_image(resolution=150)
            buf = io.BytesIO()
            img_obj.save(buf, format="PNG")
            buf.seek(0)
            return base64.standard_b64encode(buf.read()).decode("utf-8")

    def _extract_via_claude_vision(self, image_b64: str) -> str:
        """
        Send a page image to Claude Vision and return the OCR'd text.

        Uses a minimal prompt so Claude returns only the raw text,
        preserving structure as much as possible for downstream
        JSON extraction.
        """
        message = self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a page from an Odia-language voter roll PDF. "
                                "Please transcribe ALL text visible on this page exactly as it appears, "
                                "preserving the layout with each voter entry on its own block. "
                                "For each voter entry include: serial number, voter ID (NZN/KKG number), "
                                "name, father/husband name, house number, age, and gender. "
                                "Output only the raw transcribed text, no commentary."
                            ),
                        },
                    ],
                }
            ],
        )
        return message.content[0].text
