"""
API Routes - FIXED VERSION
Key fix: OCR text extraction runs BEFORE Claude processing.
The old code passed blank pdfplumber text to Claude (image-only PDF),
so all chunks failed. Now each page is rendered to an image via
pdfplumber and sent to Claude Vision to get real text first.
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
import threading

from anthropic import Anthropic

from services.pdf_chunker import PDFChunker
from services.ocr_extractor import OCRExtractor
from services.claude_processor import ClaudeProcessor
from services.excel_generator import ExcelGenerator
from utils.config import Config

api_bp = Blueprint("api", __name__, url_prefix="/api")

JOBS = {}


def process_job_background(job_id):
    """Background worker — correct pipeline order."""
    if job_id not in JOBS:
        return

    job = JOBS[job_id]

    try:
        job["status"] = "processing"
        job["progress"] = 5

        # One shared client for the whole job
        anthropic_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Step 1: Chunk PDF
        chunker = PDFChunker(
            max_chunk_tokens=Config.MAX_CHUNK_TOKENS,
            chunk_page_size=Config.CHUNK_PAGE_SIZE,
        )
        chunks, chunking_metadata = chunker.chunk_pdf(job["filepath"])
        job["progress"] = 20
        print(f"[{job_id}] Created {len(chunks)} chunks")

        # Step 2: OCR each page
        # CRITICAL FIX: pass anthropic_client so Vision OCR works for
        # image-based PDFs (pdfplumber returns empty text for these).
        ocr_extractor = OCRExtractor(
            tesseract_path=Config.TESSERACT_PATH,
            anthropic_client=anthropic_client,
        )

        extracted_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_text = ""
            for page_num in chunk.pages:
                page_text, method = ocr_extractor.extract_text_from_page(
                    job["filepath"], page_num
                )
                print(f"  Page {page_num + 1}: method={method}, chars={len(page_text)}")
                chunk_text += page_text + "\n"

            extracted_chunks.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk_text,
                "pages": chunk.pages,
            })
            job["progress"] = 20 + int((i + 1) / len(chunks) * 40)

        # Step 3: Claude extracts structured data from OCR text
        claude_processor = ClaudeProcessor(api_key=Config.ANTHROPIC_API_KEY)
        chunk_results = []

        for i, chunk_data in enumerate(extracted_chunks):
            result = claude_processor.process_chunk(
                chunk_text=chunk_data["text"],
                customer_request=job["customer_request"],
                chunk_id=chunk_data["chunk_id"],
                input_language=job["input_language"],
                output_language=job["output_language"],
            )
            chunk_results.append(result)
            print(f"  Chunk {chunk_data['chunk_id']}: success={result['success']}, records={len(result['data'])}")
            job["progress"] = 60 + int((i + 1) / len(extracted_chunks) * 25)

        # Step 4: Merge
        merged_results = claude_processor.merge_results(chunk_results)
        job["progress"] = 88
        print(f"[{job_id}] Total records: {merged_results['quality_metrics']['total_records']}")

        # Step 5: Generate Excel
        excel_path = os.path.join(Config.UPLOAD_FOLDER, f"output_{job_id}.xlsx")
        ExcelGenerator().generate_excel(
            merged_data=merged_results,
            customer_request=job["customer_request"],
            output_path=excel_path,
        )

        job["results"] = merged_results
        job["excel_path"] = excel_path
        job["status"] = "completed"
        job["progress"] = 100
        job["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        import traceback
        job["status"] = "failed"
        job["error"] = str(e)
        job["progress"] = 0
        print(f"[{job_id}] FAILED: {e}")
        traceback.print_exc()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


@api_bp.route("/upload", methods=["POST"])
def upload_pdf():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        customer_request = request.form.get("request", "")
        input_language = request.form.get("input_language", "english").lower()
        output_language = request.form.get("output_language", "english").lower()

        if not file.filename:
            return jsonify({"error": "No file selected"}), 400
        if not customer_request:
            return jsonify({"error": "Customer request is required"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        file.seek(0, os.SEEK_END)
        if file.tell() > Config.MAX_FILE_SIZE:
            return jsonify({"error": "File too large"}), 400
        file.seek(0)

        job_id = str(uuid.uuid4())
        filename = secure_filename(f"{job_id}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)

        JOBS[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "filename": filename,
            "filepath": filepath,
            "customer_request": customer_request,
            "input_language": input_language,
            "output_language": output_language,
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "results": None,
            "error": None,
        }

        threading.Thread(
            target=process_job_background, args=(job_id,), daemon=True
        ).start()

        return jsonify({
            "job_id": job_id,
            "status": "pending",
            "message": "PDF uploaded. Processing started.",
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    job = JOBS[job_id]
    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job["error"],
        "created_at": job["created_at"],
    }), 200


@api_bp.route("/download/<job_id>", methods=["GET"])
def download_excel(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    job = JOBS[job_id]
    if job["status"] != "completed":
        return jsonify({"error": f'Job is {job["status"]}, not ready'}), 400
    excel_path = job.get("excel_path")
    if not excel_path or not os.path.exists(excel_path):
        return jsonify({"error": "Excel file not found"}), 404
    return send_file(
        excel_path,
        as_attachment=True,
        download_name=f"extracted_data_{job_id}.xlsx",
    )


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0.0",
    }), 200
