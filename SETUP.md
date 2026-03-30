# Setup & Installation Guide

## System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher (optional, for frontend development)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space

## Step-by-Step Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/PETERSUNNY/pdf-to-xl-AI.git
cd pdf-to-xl-AI
```

### Step 2: Install Tesseract OCR (Required)

#### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (choose default installation path)
3. Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Step 3: Backend Setup

#### 3.1 Create Virtual Environment

**Windows:**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 3.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- flask (web framework)
- anthropic (Claude API)
- pdfplumber (PDF text extraction)
- pytesseract (OCR)
- pdf2image (PDF to image conversion)
- openpyxl (Excel generation)
- python-dotenv (configuration)

#### 3.3 Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your settings
# On Windows: notepad .env
# On macOS/Linux: nano .env
```

**Required settings:**
```env
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-v0-xxxxxxxxxxxxxxxx
```

**Optional settings (defaults are fine):**
```env
FLASK_ENV=development
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
# On macOS/Linux: /usr/local/bin/tesseract
MAX_FILE_SIZE=500000000  # 500MB
PORT=5000
```

### Step 4: Frontend Setup (Optional Dev)

If you want to develop the React frontend:

```bash
cd frontend
npm install
```

### Step 5: Verify Installation

#### Test Backend

```bash
cd backend
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

Open browser → `http://localhost:5000`

#### Test Python Dependencies

```powershell
python -c "import pdfplumber; import pytesseract; import anthropic; print('All imports OK')"
```

#### Test Tesseract

```powershell
tesseract --version
```

## Getting Claude API Key

1. Go to: https://console.anthropic.com/
2. Sign up / Log in
3. Navigate to "API Keys"
4. Create new API key
5. Copy and paste into `.env` file

## Running the Application

### Start Backend Server

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

Server runs on: **http://localhost:5000**

### (Optional) Start Frontend Dev Server

In another terminal:
```bash
cd frontend
npm start
```

Frontend runs on: **http://localhost:3000** (optional development)

## Building for Production

### Build Frontend

```bash
cd frontend
npm run build
```

This creates optimized build in `frontend/build/`

### Environment for Production

Create production `.env`:
```env
FLASK_ENV=production
SECRET_KEY=<generate-random-string>
ANTHROPIC_API_KEY=<your-key>
DEBUG=False
```

Generate secure key:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run Production Server

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## Docker Setup (Optional)

### Build Docker Image

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Copy backend
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy app
COPY backend/ .

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t pdf-to-excel .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=your_key pdf-to-excel
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pdfplumber'"
**Solution**: Ensure virtual environment is activated and dependencies installed
```bash
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "pytesseract.TesseractNotFoundError"
**Solution**: Tesseract not installed or path incorrect
1. Verify Tesseract installation: `tesseract --version`
2. Update `TESSERACT_PATH` in `.env`
3. Restart application

### Issue: "ANTHROPIC_API_KEY not found"
**Solution**: Add API key to `.env` file
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### Issue: Port 5000 already in use
**Solution**: Change port in `.env` or kill process using port
```bash
# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

### Issue: Large PDF hangs/times out
**Solution**: Expected behavior for large files
- 5-10MB PDFs: 2-5 minutes
- 20-50MB PDFs: 5-15 minutes
- 100+MB PDFs: 15-30+ minutes

## Useful Commands

### Check Python Version
```bash
python --version
```

### Check Node Version
```bash
node --version
npm --version
```

### List Installed Python Packages
```bash
pip list
```

### Update Python Packages
```bash
pip install --upgrade -r requirements.txt
```

### Format Python Code
```bash
pip install black
black backend/
```

### Run Tests
```bash
# Add pytest to requirements.txt first
pip install pytest
pytest backend/tests/
```

## Next Steps

1. ✅ Installation complete!
2. 📖 Read README.md for feature overview
3. 🚀 Start using the application
4. 🐛 Report issues on GitHub
5. 🔄 Contribute improvements!

## Support

- **Documentation**: See README.md
- **Issues**: GitHub Issues
- **Cloud API Docs**: https://docs.anthropic.com/
- **Flask Docs**: https://flask.palletsprojects.com/
