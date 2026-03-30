"""
OCR Extractor Service
Handles text extraction from PDFs, supporting both:
1. Selectable text (using pdfplumber)
2. Scanned images (using Tesseract OCR)
"""

import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
from typing import Tuple, Dict
import os

class OCRExtractor:
    def __init__(self, tesseract_path: str = None):
        """Initialize OCR extractor with Tesseract path"""
        if tesseract_path:
            pytesseract.pytesseract.pytesseract_cmd = tesseract_path
    
    def extract_text_from_page(self, pdf_path: str, page_num: int) -> Tuple[str, str]:
        """
        Extract text from a single PDF page using best-fit method.
        
        Returns:
            - Extracted text
            - Method used ('pdfplumber' or 'tesseract')
        """
        # First try pdfplumber (fast, for selectable text)
        pdfplumber_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    # If text is substantial, use it
                    if text and len(text.strip()) > 0:
                        pdfplumber_text = text
                        # Return if we have meaningful text (even if small)
                        if len(text.strip()) > 20:
                            return text, 'pdfplumber'
        except Exception as e:
            pass  # Silently continue to OCR fallback
        
        # Fallback to OCR for scanned pages
        fallback = False
        try:
            text = self._extract_via_ocr(pdf_path, page_num)
            if text and len(text.strip()) > 0:
                return text, 'tesseract'
            fallback = True
        except Exception as e:
            fallback = True
        
        # If OCR failed or returned nothing, use pdfplumber result even if small
        if pdfplumber_text:
            return pdfplumber_text, 'pdfplumber'
        
        return "", "failed"
    
    def _extract_via_ocr(self, pdf_path: str, page_num: int) -> str:
        """Extract text from PDF page using Tesseract OCR"""
        try:
            # Convert PDF page to image
            try:
                images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
            except Exception as poppler_error:
                if "poppler" in str(poppler_error).lower():
                    # Poppler not installed, skip OCR
                    return ""
                raise
            
            if not images:
                return ""
            
            # Run OCR on image
            text = pytesseract.image_to_string(images[0])
            return text
        except Exception as e:
            if "poppler" not in str(e).lower():
                print(f"OCR extraction failed: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from entire PDF using hybrid approach.
        
        Returns:
            - Full text from all pages
            - Metadata dict with extraction stats
        """
        full_text = ""
        metadata = {
            'total_pages': 0,
            'pdfplumber_pages': 0,
            'ocr_pages': 0,
            'failed_pages': 0,
            'extraction_methods': {}
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata['total_pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    text, method = self.extract_text_from_page(pdf_path, page_num)
                    
                    full_text += f"\n--- Page {page_num + 1} ({method}) ---\n"
                    full_text += text
                    
                    # Track stats
                    if method == 'pdfplumber':
                        metadata['pdfplumber_pages'] += 1
                    elif method == 'tesseract':
                        metadata['ocr_pages'] += 1
                    else:
                        metadata['failed_pages'] += 1
        
        except Exception as e:
            print(f"Error processing PDF: {e}")
        
        return full_text, metadata
