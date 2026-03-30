# PDF-to-Excel AI Extraction Bot

A powerful web-based tool that converts PDFs into structured Excel files using Claude AI. Handles both regular and scanned PDFs with OCR support.

## 🎯 Features

- **PDF Upload & Processing**: Upload PDFs up to 500MB
- **Intelligent Chunking**: Automatically breaks large files into manageable chunks
- **OCR Support**: Handles both text-enabled and scanned PDFs
- **AI-Powered Extraction**: Uses Claude AI to intelligently extract and structure data
- **Excel Generation**: Creates formatted Excel workbooks with extracted data
- **Real-time Progress**: Live updates during processing
- **User-Friendly UI**: Modern, responsive web interface

## 🏗️ Architecture

```
pdf-to-xl-AI/
├── backend/           # Flask API server
│   ├── app.py        # Main application entry point
│   ├── requirements.txt
│   ├── .env.example  # Configuration template
│   ├── api/          # API routes
│   ├── services/     # Core business logic
│   │   ├── pdf_chunker.py        # PDF splitting
│   │   ├── ocr_extractor.py      # Text extraction with OCR
│   │   ├── claude_processor.py   # AI data extraction
│   │   └── excel_generator.py    # Excel file creation
│   └── utils/        # Utilities
│       └── config.py # Configuration management
│
├── frontend/          # React web application
│   ├── public/       # Static assets
│   ├── src/
│   │   ├── App.jsx   # Main app component
│   │   └── components/
│   │       ├── UploadForm.jsx          # PDF upload interface
│   │       ├── ProgressTracker.jsx     # Processing progress
│   │       └── ResultDisplay.jsx       # Results and download
│   └── package.json
│
└── README.md
```

## 🚀 Quick Start

See **[SETUP.md](SETUP.md)** for detailed installation instructions.

### TL;DR (Quick Setup)

```bash
# 1. Install Tesseract (required for OCR)
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# 2. Clone repo
git clone https://github.com/PETERSUNNY/pdf-to-xl-AI.git
cd pdf-to-xl-AI

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# 5. Run
python app.py
```

Visit: **http://localhost:5000**

## 💡 How It Works

### Processing Pipeline

1. **Upload**: User uploads PDF + specifies extraction request
   - Example: "Extract voter names, phone numbers, and addresses"

2. **Chunking**: Large PDFs split into manageable chunks
   - Small (<5MB): Single chunk
   - Medium (5-20MB): ~10 pages per chunk
   - Large (>20MB): ~5 pages per chunk

3. **Text Extraction**: Hybrid approach
   - Selectable text → pdfplumber
   - Scanned pages → Tesseract OCR
   - Automatic method selection

4. **AI Processing**: Claude API processes each chunk
   - Extracts structured data per request
   - Returns JSON format

5. **Result Merging**: Combines all chunk results
   - Normalizes field schemas
   - Validates consistency
   - Creates unified dataset

6. **Excel Generation**: Creates formatted workbook
   - Sheet 1: Processing metadata
   - Sheet 2: Extracted data with headers

7. **Download**: User downloads Excel file

## 📊 Example Use Cases

- **Voter Data**: Extract and structure voter lists
- **Invoices**: Digitize invoice details from PDFs
- **Surveys**: Convert paper surveys to Excel
- **Contacts**: Digitize contact lists
- **Reports**: Extract metrics from reports

## 🔌 API Endpoints

```bash
# Upload PDF
POST /api/upload
  Body: file (PDF), request (text)
  Returns: { job_id, status }

# Check Status
GET /api/status/<job_id>
  Returns: { status, progress, error }

# Download Excel
GET /api/download/<job_id>
  Returns: Excel file

# Health Check
GET /api/health
  Returns: { status }
```

## ⚙️ Configuration

Edit `backend/.env`:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
FLASK_ENV=development
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
MAX_FILE_SIZE=500000000  # 500MB
UPLOAD_FOLDER=./uploads
MAX_CHUNK_TOKENS=50000
CHUNK_PAGE_SIZE=10
PORT=5000
```

## 🧪 Testing

```python
# Test PDF chunking
from services.pdf_chunker import PDFChunker

chunker = PDFChunker()
chunks, metadata = chunker.chunk_pdf("test.pdf")
print(f"Created {len(chunks)} chunks")

# Test Claude processing
from services.claude_processor import ClaudeProcessor

processor = ClaudeProcessor(api_key="your-key")
result = processor.process_chunk(
    chunk_text=chunks[0].text,
    customer_request="Extract names",
    chunk_id=0
)
```

## 📈 Performance

- **Small PDF (<5MB)**: ~2-3 minutes
- **Medium PDF (5-20MB)**: ~5-8 minutes
- **Large PDF (20-100MB)**: ~10-30 minutes

*Processing time depends on PDF complexity and Claude API*

## 🔒 Security

- ✅ API key in `.env` (not in code)
- ✅ File uploads limited to 500MB
- ✅ Temporary upload storage
- ⚠️ TODO: User authentication for production
- ⚠️ TODO: Rate limiting
- ⚠️ TODO: File cleanup jobs

## 🐛 Troubleshooting

### "pytesseract.TesseractNotFoundError"
→ Install Tesseract and verify `TESSERACT_PATH` in `.env`

### "ModuleNotFoundError"
→ Activate venv: `source venv/bin/activate`

### "ANTHROPIC_API_KEY not found"
→ Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

See **[SETUP.md](SETUP.md)** for more troubleshooting

## 📝 Tech Stack

- **Backend**: Flask, Flask-CORS
- **AI**: Claude API (Anthropic)
- **PDF Processing**: pdfplumber, PyPDF2
- **OCR**: Tesseract, pdf2image, Pillow
- **Excel**: openpyxl
- **Frontend**: React 18, Axios
- **Configuration**: python-dotenv

## 🚀 Production Deployment

See **[SETUP.md](SETUP.md)** for Docker and production setup

## 📋 Roadmap

- [ ] Background job processing (Celery/Redis)
- [ ] Database integration (PostgreSQL)
- [ ] User authentication & profiles
- [ ] Rate limiting & quotas
- [ ] CSV/JSON export formats
- [ ] Batch processing multiple PDFs
- [ ] Custom validation rules
- [ ] Support for password-protected PDFs
- [ ] Advanced chunking strategies

## 🤝 Contributing

Contributions welcome! Feel free to submit issues and PRs.

## 📞 Support

For issues:
1. Check [SETUP.md](SETUP.md) troubleshooting section
2. Verify `.env` configuration
3. Review error logs
4. Check API documentation

## 📄 License

MIT License - Use freely

---

**Built with**: Flask • React • Claude AI • Tesseract • pdfplumber • openpyxl