"""
Claude Processor Service
Handles communication with Claude API for data extraction
from PDF chunks and customer requests.
"""

from anthropic import Anthropic
from typing import Dict, List
import json
import re

class ClaudeProcessor:
    def __init__(self, api_key: str):
        """Initialize Claude processor with API key"""
        self.client = Anthropic()
        self.api_key = api_key
    
    def process_chunk(self, chunk_text: str, customer_request: str, chunk_id: int, input_language: str = "english", output_language: str = "english") -> Dict:
        """
        Process a single PDF chunk with customer request.
        
        Args:
            chunk_text: Extracted text from PDF chunk
            customer_request: User's data extraction request (e.g., "extract voter names and addresses")
            chunk_id: Identifier for this chunk
        
        Returns:
            Dict with:
            - success: bool
            - data: structured data or raw text
            - fields: list of field names extracted
            - error: error message if failed
            - token_usage: token count
        """
        result = {
            'chunk_id': chunk_id,
            'success': False,
            'data': [],
            'fields': [],
            'error': None,
            'token_usage': 0,
            'method': 'claude'
        }
        
        system_prompt = """You are a specialized data extraction expert with multi-language support. Your task is to:
1. If the content is in a different language, translate it to the target language
2. Extract data from the provided PDF content according to the user's request
3. Format the extracted data as a JSON array of objects
4. Each object represents a row of data with consistent field names
5. Use descriptive field names (e.g., 'voter_name', 'phone_number', 'address')
6. Return ONLY valid JSON, no other text
7. If data is not available, use null values
8. Preserve original data formatting (dates, numbers, etc.)

IMPORTANT: Return ONLY the JSON array, nothing else."""
        
        language_instruction = ""
        if input_language.lower() != "english" or output_language.lower() != "english":
            language_instruction = f"\n\nLANGUAGE INSTRUCTION: The PDF content is in {input_language}. Please translate to {output_language} before extracting data."
        
        user_prompt = f"""Extract data from the following PDF content according to this request:

REQUEST: {customer_request}{language_instruction}

PDF CONTENT:
{chunk_text}

Return the extracted data as a JSON array of objects with consistent field names."""
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = message.content[0].text
            result['token_usage'] = message.usage.input_tokens + message.usage.output_tokens
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    result['data'] = data if isinstance(data, list) else [data]
                    result['success'] = True
                    
                    # Extract field names
                    if result['data'] and len(result['data']) > 0:
                        result['fields'] = list(result['data'][0].keys())
                else:
                    result['error'] = 'No JSON found in response'
                    result['data'] = [{'raw_text': response_text}]
                    result['fields'] = ['raw_text']
                    result['success'] = False
            
            except json.JSONDecodeError as e:
                result['error'] = f'JSON parsing error: {str(e)}'
                result['data'] = [{'raw_text': response_text}]
                result['fields'] = ['raw_text']
                result['success'] = False
        
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    def merge_results(self, chunk_results: List[Dict]) -> Dict:
        """
        Merge results from multiple chunks into single dataset.
        
        Args:
            chunk_results: List of results from process_chunk()
        
        Returns:
            Dict with:
            - merged_data: combined list of records
            - field_schema: unified field names
            - quality_metrics: statistics about merge
        """
        merged_data = []
        all_fields = set()
        chunk_errors = []
        successful_chunks = 0
        
        for result in chunk_results:
            if result['success']:
                successful_chunks += 1
                merged_data.extend(result['data'])
                all_fields.update(result['fields'])
            else:
                chunk_errors.append({
                    'chunk_id': result['chunk_id'],
                    'error': result['error']
                })
        
        # Normalize all records to include all fields
        normalized_data = []
        for record in merged_data:
            normalized_record = {field: record.get(field, None) for field in all_fields}
            normalized_data.append(normalized_record)
        
        return {
            'merged_data': normalized_data,
            'field_schema': sorted(list(all_fields)),
            'quality_metrics': {
                'total_chunks': len(chunk_results),
                'successful_chunks': successful_chunks,
                'failed_chunks': len(chunk_errors),
                'total_records': len(normalized_data),
                'field_count': len(all_fields)
            },
            'chunk_errors': chunk_errors
        }
