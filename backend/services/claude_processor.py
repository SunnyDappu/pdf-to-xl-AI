"""
Claude Processor Service
Handles communication with Claude API for data extraction
from PDF chunks and customer requests.

BUG FIXES:
- __init__ created self.client = Anthropic() without passing api_key,
  then stored api_key separately but never used it.
  Anthropic() with no arguments works only if ANTHROPIC_API_KEY env-var
  is set.  Fixed to: self.client = Anthropic(api_key=api_key) so the
  key passed in is actually used.

- process_chunk() sent empty/whitespace-only chunk_text to Claude when
  pdfplumber returned nothing (image-only PDF).  Now returns an early
  error result if chunk_text is blank, so callers know to use OCR first.

- merge_results() regex r'\[.*\]' is inside process_chunk — kept as-is
  but added a fallback for JSON objects ({...}) in case Claude wraps
  a single record in braces instead of an array.
"""

from anthropic import Anthropic
from typing import Dict, List
import json
import re


class ClaudeProcessor:
    def __init__(self, api_key: str):
        """Initialize Claude processor with API key."""
        # BUG FIX: was Anthropic() — api_key was stored but never passed in
        self.client = Anthropic(api_key=api_key)
        self.api_key = api_key

    def process_chunk(
        self,
        chunk_text: str,
        customer_request: str,
        chunk_id: int,
        input_language: str = "english",
        output_language: str = "english",
    ) -> Dict:
        """
        Process a single PDF chunk with the customer's extraction request.

        Returns dict with keys:
            chunk_id, success, data, fields, error, token_usage, method
        """
        result = {
            "chunk_id": chunk_id,
            "success": False,
            "data": [],
            "fields": [],
            "error": None,
            "token_usage": 0,
            "method": "claude",
        }

        # BUG FIX: image-only PDFs produce blank chunk_text after pdfplumber.
        # Sending blank text to Claude wastes tokens and returns an empty array.
        # Callers should run OCRExtractor first; if they don't, bail early.
        if not chunk_text or not chunk_text.strip():
            result["error"] = (
                "chunk_text is empty — this PDF page is image-based. "
                "Run OCRExtractor.extract_text_from_page() before calling process_chunk()."
            )
            return result

        system_prompt = (
            "You are a specialized data extraction expert with multi-language support. "
            "Your task is to:\n"
            "1. If the content is in a different language, translate it to the target language.\n"
            "2. Extract data from the provided PDF content according to the user's request.\n"
            "3. Format the extracted data as a JSON array of objects.\n"
            "4. Each object represents one row of data with consistent field names.\n"
            "5. Use descriptive English field names (e.g. voter_name, father_name, house_no, age, gender, voter_id).\n"
            "6. Return ONLY valid JSON — no markdown fences, no explanation.\n"
            "7. If a field is not available use null.\n"
            "8. Preserve original formatting of dates and numbers.\n\n"
            "IMPORTANT: Return ONLY the JSON array, nothing else."
        )

        language_instruction = ""
        if input_language.lower() != "english" or output_language.lower() != "english":
            language_instruction = (
                f"\n\nLANGUAGE INSTRUCTION: The PDF content is in {input_language}. "
                f"Please translate all extracted values to {output_language}."
            )

        user_prompt = (
            f"Extract data from the following PDF content according to this request:\n\n"
            f"REQUEST: {customer_request}{language_instruction}\n\n"
            f"PDF CONTENT:\n{chunk_text}\n\n"
            f"Return the extracted data as a JSON array of objects with consistent field names."
        )

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = message.content[0].text
            result["token_usage"] = (
                message.usage.input_tokens + message.usage.output_tokens
            )

            # Strip markdown code fences if present
            response_text = re.sub(r"```(?:json)?", "", response_text).strip()

            # Try array first, then single object
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if not json_match:
                # Fallback: maybe Claude returned a single object
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, dict):
                    parsed = [parsed]
                result["data"] = parsed
                result["success"] = True
                if result["data"]:
                    result["fields"] = list(result["data"][0].keys())
            else:
                result["error"] = "No JSON found in Claude response"
                result["data"] = [{"raw_text": response_text}]
                result["fields"] = ["raw_text"]

        except json.JSONDecodeError as e:
            result["error"] = f"JSON parsing error: {e}"
            result["data"] = [{"raw_text": response_text}]
            result["fields"] = ["raw_text"]

        except Exception as e:
            result["error"] = str(e)

        return result

    def merge_results(self, chunk_results: List[Dict]) -> Dict:
        """
        Merge results from multiple chunks into a single dataset.
        """
        merged_data = []
        all_fields: set = set()
        chunk_errors = []
        successful_chunks = 0

        for result in chunk_results:
            if result["success"]:
                successful_chunks += 1
                merged_data.extend(result["data"])
                all_fields.update(result["fields"])
            else:
                chunk_errors.append(
                    {"chunk_id": result["chunk_id"], "error": result["error"]}
                )

        # Normalise: every record gets every field (None for missing)
        normalized_data = [
            {field: record.get(field) for field in all_fields}
            for record in merged_data
        ]

        return {
            "merged_data": normalized_data,
            "field_schema": sorted(list(all_fields)),
            "quality_metrics": {
                "total_chunks": len(chunk_results),
                "successful_chunks": successful_chunks,
                "failed_chunks": len(chunk_errors),
                "total_records": len(normalized_data),
                "field_count": len(all_fields),
            },
            "chunk_errors": chunk_errors,
        }
