import React, { useState } from 'react';
import axios from 'axios';
import './UploadForm.css';

function UploadForm({ onUpload }) {
  const [file, setFile] = useState(null);
  const [request, setRequest] = useState('');
  const [inputLanguage, setInputLanguage] = useState('english');
  const [outputLanguage, setOutputLanguage] = useState('english');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const languages = [
    { code: 'english', name: 'English' },
    { code: 'odia', name: 'Odia (ଓଡ଼ିଆ)' },
    { code: 'hindi', name: 'Hindi (हिंदी)' },
    { code: 'bengali', name: 'Bengali (বাংলা)' },
    { code: 'tamil', name: 'Tamil (தமிழ்)' },
    { code: 'telugu', name: 'Telugu (తెలుగు)' },
    { code: 'kannada', name: 'Kannada (ಕನ್ನಡ)' },
    { code: 'malayalam', name: 'Malayalam (മലയാളം)' },
    { code: 'gujarati', name: 'Gujarati (ગુજરાતી)' },
    { code: 'punjabi', name: 'Punjabi (ਪੰਜਾਬੀ)' },
    { code: 'urdu', name: 'Urdu (اردو)' },
    { code: 'marathi', name: 'Marathi (मराठी)' },
    { code: 'spanish', name: 'Spanish (Español)' },
    { code: 'french', name: 'French (Français)' },
    { code: 'german', name: 'German (Deutsch)' },
    { code: 'chinese', name: 'Chinese (中文)' },
    { code: 'japanese', name: 'Japanese (日本語)' },
    { code: 'korean', name: 'Korean (한국어)' },
    { code: 'russian', name: 'Russian (Русский)' },
    { code: 'arabic', name: 'Arabic (العربية)' },
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a PDF file');
      return;
    }
    
    if (!request.trim()) {
      setError('Please enter what you want to extract from the PDF');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('request', request);
      formData.append('input_language', inputLanguage);
      formData.append('output_language', outputLanguage);

      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.job_id) {
        onUpload(response.data.job_id);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-form-container">
      <div className="upload-card">
        <form onSubmit={handleSubmit} className="upload-form">
          
          {/* File Upload Section */}
          <div
            className={`upload-area ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-input"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={loading}
              style={{ display: 'none' }}
            />
            <label htmlFor="file-input" className="upload-label">
              <div className="upload-icon">📁</div>
              <h3>Drag and drop your PDF here</h3>
              <p>or click to select a file</p>
              {file && <p className="file-name">Selected: {file.name}</p>}
            </label>
          </div>

          {/* Request Input Section */}
          <div className="request-section">
            <label htmlFor="request" className="label">
              What do you want to extract?
            </label>
            <textarea
              id="request"
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              placeholder="Example: Extract all voter names, phone numbers, and addresses. Format as columns in Excel."
              disabled={loading}
              rows={4}
              className="request-input"
            />
            <p className="helper-text">
              Be specific about what data you want and how you want it formatted
            </p>
          </div>

          {/* Language Selection Section */}
          <div className="language-section">
            <div className="language-group">
              <label htmlFor="input-language" className="label">
                📄 PDF Language
              </label>
              <select
                id="input-language"
                value={inputLanguage}
                onChange={(e) => setInputLanguage(e.target.value)}
                disabled={loading}
                className="language-select"
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="language-arrow">→</div>

            <div className="language-group">
              <label htmlFor="output-language" className="label">
                📊 Excel Language
              </label>
              <select
                id="output-language"
                value={outputLanguage}
                onChange={(e) => setOutputLanguage(e.target.value)}
                disabled={loading}
                className="language-select"
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Error Message */}
          {error && <div className="error-message">{error}</div>}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !file}
            className="btn-submit"
          >
            {loading ? 'Uploading...' : 'Start Processing'}
          </button>

          <p className="note">
            ℹ️ Supports PDF files up to 500MB. Processing time depends on file size.
          </p>
        </form>
      </div>
    </div>
  );
}

export default UploadForm;
