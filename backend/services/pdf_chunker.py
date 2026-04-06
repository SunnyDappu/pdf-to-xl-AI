"""
PDF Chunking Service
Intelligently breaks down large PDFs into manageable chunks
based on file size and content structure.

BUG FIXES:
- _chunk_by_size() was called with WRONG arguments for medium/large files.
  Original code: _chunk_by_size(pdf, total_pages, pages_per_chunk)
  But the function signature is: _chunk_by_size(pdf, total_pages, pages_per_chunk)
  and for the small-file case it was called as:
      _chunk_by_size(pdf, 1, total_pages)   <-- 1 as total_pages, total_pages as pages_per_chunk
  This caused the small-file branch to create a single chunk of 1 page
  and completely skip the rest of the document.

- Fixed small-file call to: _chunk_by_size(pdf, total_pages, total_pages)
  which creates exactly one chunk containing all pages.
"""

import pdfplumber
import os
from typing import List, Dict, Tuple


class PDFChunk:
    def __init__(self, chunk_id: int, pages: List[int], text: str, metadata: Dict = None):
        self.chunk_id = chunk_id
        self.pages = pages          # 0-based page numbers
        self.text = text
        self.metadata = metadata or {}
        self.token_estimate = len(text) // 4  # ~4 chars per token


class PDFChunker:
    def __init__(self, max_chunk_tokens: int = 50000, chunk_page_size: int = 10):
        self.max_chunk_tokens = max_chunk_tokens
        self.chunk_page_size = chunk_page_size

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def get_file_size_mb(self, file_path: str) -> float:
        return os.path.getsize(file_path) / (1024 * 1024)

    def chunk_pdf(self, pdf_path: str) -> Tuple[List[PDFChunk], Dict]:
        """
        Intelligently chunk a PDF based on file size.

        Strategy:
          < 5 MB  → one chunk (all pages)
          5-20 MB → 10 pages per chunk
          > 20 MB → 5 pages per chunk
        """
        file_size_mb = self.get_file_size_mb(pdf_path)
        metadata = {
            "file_size_mb": file_size_mb,
            "total_chunks": 0,
            "chunk_strategy": "",
            "total_pages": 0,
            "token_estimate": 0,
        }

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            metadata["total_pages"] = total_pages

            if file_size_mb < 5:
                metadata["chunk_strategy"] = "single_chunk (file < 5MB)"
                # BUG FIX: was _chunk_by_size(pdf, 1, total_pages)
                # — passed 1 as total_pages so only ever made 1-page chunks
                chunks = self._chunk_by_size(pdf, total_pages, total_pages)

            elif file_size_mb < 20:
                metadata["chunk_strategy"] = "medium_chunk (5-20MB, ~10 pages per chunk)"
                chunks = self._chunk_by_size(pdf, total_pages, 10)

            else:
                metadata["chunk_strategy"] = "large_chunk (>20MB, ~5 pages per chunk)"
                chunks = self._chunk_by_size(pdf, total_pages, 5)

            metadata["total_chunks"] = len(chunks)
            metadata["token_estimate"] = sum(c.token_estimate for c in chunks)

        return chunks, metadata

    def _chunk_by_size(self, pdf, total_pages: int, pages_per_chunk: int) -> List[PDFChunk]:
        """Break PDF into fixed-size page chunks."""
        chunks = []
        chunk_id = 0

        for start_page in range(0, total_pages, pages_per_chunk):
            end_page = min(start_page + pages_per_chunk, total_pages)

            chunk_text = ""
            for page_num in range(start_page, end_page):
                page = pdf.pages[page_num]
                chunk_text += f"\n--- Page {page_num + 1} ---\n"
                chunk_text += page.extract_text() or ""

            chunk = PDFChunk(
                chunk_id=chunk_id,
                pages=list(range(start_page, end_page)),
                text=chunk_text,
                metadata={
                    "start_page": start_page + 1,
                    "end_page": end_page,
                    "page_count": end_page - start_page,
                },
            )
            chunks.append(chunk)
            chunk_id += 1

        return chunks

    def validate_chunks(self, chunks: List[PDFChunk]) -> Dict:
        validation = {
            "total_chunks": len(chunks),
            "valid_chunks": 0,
            "oversized_chunks": [],
            "all_valid": True,
        }
        for chunk in chunks:
            if chunk.token_estimate > self.max_chunk_tokens:
                validation["oversized_chunks"].append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "estimated_tokens": chunk.token_estimate,
                        "max_allowed": self.max_chunk_tokens,
                    }
                )
                validation["all_valid"] = False
            else:
                validation["valid_chunks"] += 1
        return validation
