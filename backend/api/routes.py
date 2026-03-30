"""
API Routes
Handles HTTP endpoints for PDF upload, processing, and download.
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
import json
import threading

from services.pdf_chunker import PDFChunker
from services.ocr_extractor import OCRExtractor
from services.claude_processor import ClaudeProcessor
from services.excel_generator import ExcelGenerator
from utils.config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')

# In-memory job storage (replace with database in production)
JOBS = {}

def process_job_background(job_id):
    """Background worker to process a PDF job"""
    if job_id not in JOBS:
        return
    
    job = JOBS[job_id]
    
    try:
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Step 1: Chunk PDF
        chunker = PDFChunker(
            max_chunk_tokens=Config.MAX_CHUNK_TOKENS,
            chunk_page_size=Config.CHUNK_PAGE_SIZE
        )
        chunks, chunking_metadata = chunker.chunk_pdf(job['filepath'])
        job['progress'] = 25
        
        # Step 2: Extract text from chunks (with OCR for scanned content)
        ocr_extractor = OCRExtractor(tesseract_path=Config.TESSERACT_PATH)
        extracted_chunks = []
        for i, chunk in enumerate(chunks):
            # Extract text from each page in the chunk and combine
            chunk_text = ""
            for page_num in chunk.pages:
                page_text, method = ocr_extractor.extract_text_from_page(
                    job['filepath'], 
                    page_num
                )
                chunk_text += page_text + "\n"
            
            extracted_chunks.append({
                'chunk_id': chunk.chunk_id,
                'text': chunk_text,
                'pages': chunk.pages
            })
            job['progress'] = 25 + int((i + 1) / len(chunks) * 25)
        
        # Step 3: Process chunks with Claude
        claude_processor = ClaudeProcessor(api_key=Config.ANTHROPIC_API_KEY)
        chunk_results = []
        
        for i, chunk_data in enumerate(extracted_chunks):
            result = claude_processor.process_chunk(
                chunk_text=chunk_data['text'],
                customer_request=job['customer_request'],
                chunk_id=chunk_data['chunk_id'],
                input_language=job['input_language'],
                output_language=job['output_language']
            )
            chunk_results.append(result)
            job['progress'] = 50 + int((i + 1) / len(extracted_chunks) * 25)
        
        # Merge results from all chunks
        merged_results = claude_processor.merge_results(chunk_results)
        job['progress'] = 80
        
        # Step 4: Generate Excel
        excel_generator = ExcelGenerator()
        excel_path = os.path.join(
            Config.UPLOAD_FOLDER,
            f"output_{job_id}.xlsx"
        )
        excel_generator.generate_excel(
            merged_data=merged_results,
            customer_request=job['customer_request'],
            output_path=excel_path
        )
        job['progress'] = 95
        
        # Store result
        job['results'] = merged_results
        job['excel_path'] = excel_path
        job['status'] = 'completed'
        job['progress'] = 100
        job['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        import traceback
        job['status'] = 'failed'
        job['error'] = str(e)
        job['progress'] = 0
        print(f"Job {job_id} failed: {str(e)}")
        traceback.print_exc()

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api_bp.route('/upload', methods=['POST'])
def upload_pdf():
    """
    Upload PDF and customer request.
    
    Returns:
        - job_id: Unique identifier for this job
        - status: Processing status
    """
    try:
        # Validate file and request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        customer_request = request.form.get('request', '')
        input_language = request.form.get('input_language', 'english').lower()
        output_language = request.form.get('output_language', 'english').lower()
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not customer_request:
            return jsonify({'error': 'Customer request is required'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        if file_size > Config.MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Max size: {Config.MAX_FILE_SIZE / 1000000}MB'}), 400
        file.seek(0)
        
        # Create job
        job_id = str(uuid.uuid4())
        filename = secure_filename(f"{job_id}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Save file
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)
        
        # Store job info
        JOBS[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'filename': filename,
            'filepath': filepath,
            'customer_request': customer_request,
            'input_language': input_language,
            'output_language': output_language,
            'created_at': datetime.now().isoformat(),
            'progress': 0,
            'results': None,
            'error': None
        }
        
        # Start background processing task
        worker = threading.Thread(
            target=process_job_background,
            args=(job_id,),
            daemon=True
        )
        worker.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'PDF uploaded successfully. Processing will begin shortly.'
        }), 202
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get processing status of a job"""
    if job_id not in JOBS:
        return jsonify({'error': 'Job not found'}), 404
    
    job = JOBS[job_id]
    return jsonify({
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'error': job['error'],
        'created_at': job['created_at']
    }), 200

@api_bp.route('/download/<job_id>', methods=['GET'])
def download_excel(job_id):
    """Download processed Excel file"""
    if job_id not in JOBS:
        return jsonify({'error': 'Job not found'}), 404
    
    job = JOBS[job_id]
    
    if job['status'] != 'completed':
        return jsonify({'error': f'Job still {job["status"]}. Cannot download yet.'}), 400
    
    excel_path = job.get('excel_path')
    if not excel_path or not os.path.exists(excel_path):
        return jsonify({'error': 'Excel file not found'}), 404
    
    return send_file(
        excel_path,
        as_attachment=True,
        download_name=f"extracted_data_{job_id}.xlsx"
    )

@api_bp.route('/process/<job_id>', methods=['POST'])
def process_job(job_id):
    """
    (Development/Testing) Process a job synchronously.
    In production, this should be a background task.
    """
    if job_id not in JOBS:
        return jsonify({'error': 'Job not found'}), 404
    
    job = JOBS[job_id]
    
    try:
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Step 1: Chunk PDF
        chunker = PDFChunker(
            max_chunk_tokens=Config.MAX_CHUNK_TOKENS,
            chunk_page_size=Config.CHUNK_PAGE_SIZE
        )
        chunks, chunking_metadata = chunker.chunk_pdf(job['filepath'])
        job['progress'] = 25
        
        # Step 2: Extract text from chunks (with OCR fallback)
        ocr_extractor = OCRExtractor(tesseract_path=Config.TESSERACT_PATH)
        extracted_chunks = []
        
        for idx, chunk in enumerate(chunks):
            # Use OCR extractor to get better text
            extracted_text = chunk.text  # Could use OCR here for enhanced extraction
            extracted_chunks.append({
                'chunk_id': chunk.chunk_id,
                'text': extracted_text,
                'pages': chunk.pages,
                'metadata': chunk.metadata
            })
            job['progress'] = 25 + (50 * (idx + 1) / len(chunks))
        
        # Step 3: Process chunks with Claude
        processor = ClaudeProcessor(api_key=Config.ANTHROPIC_API_KEY)
        chunk_results = []
        
        for idx, extracted_chunk in enumerate(extracted_chunks):
            result = processor.process_chunk(
                chunk_text=extracted_chunk['text'],
                customer_request=job['customer_request'],
                chunk_id=extracted_chunk['chunk_id'],
                input_language=job['input_language'],
                output_language=job['output_language']
            )
            chunk_results.append(result)
            job['progress'] = 75 + (20 * (idx + 1) / len(extracted_chunks))
        
        # Step 4: Merge results
        merged_results = processor.merge_results(chunk_results)
        job['progress'] = 90
        
        # Step 5: Generate Excel
        generator = ExcelGenerator()
        excel_filename = f"extracted_data_{job_id}.xlsx"
        excel_path = os.path.join(Config.UPLOAD_FOLDER, excel_filename)
        
        success = generator.generate_excel(
            merged_data=merged_results,
            customer_request=job['customer_request'],
            output_path=excel_path
        )
        
        if success:
            job['status'] = 'completed'
            job['progress'] = 100
            job['excel_path'] = excel_path
            job['results'] = merged_results
            job['chunking_metadata'] = chunking_metadata
        else:
            job['status'] = 'failed'
            job['error'] = 'Failed to generate Excel file'
        
        return jsonify(job), 200
    
    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        return jsonify(job), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_version': '1.0.0'
    }), 200
