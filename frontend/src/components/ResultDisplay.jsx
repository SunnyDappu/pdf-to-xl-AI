import React from 'react';
import axios from 'axios';
import './ResultDisplay.css';

function ResultDisplay({ jobId, onReset }) {
  const handleDownload = async () => {
    try {
      const response = await axios.get(`/api/download/${jobId}`, {
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `extracted_data_${jobId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download Excel file');
    }
  };

  return (
    <div className="result-display">
      <div className="result-card">
        <div className="result-header">
          <span className="result-icon">✅</span>
          <h2>Processing Complete!</h2>
        </div>

        <div className="result-content">
          <p className="result-message">
            Your PDF has been successfully processed and converted to Excel.
          </p>

          <div className="action-buttons">
            <button onClick={handleDownload} className="btn-download">
              📥 Download Excel File
            </button>
            <button onClick={onReset} className="btn-new">
              🔄 Process Another PDF
            </button>
          </div>

          <div className="next-steps">
            <h3>What's Next?</h3>
            <ul>
              <li>✓ Download your Excel file with extracted data</li>
              <li>✓ First sheet contains metadata about the processing</li>
              <li>✓ Second sheet contains all extracted data</li>
              <li>✓ Data is organized in columns for easy analysis</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResultDisplay;
