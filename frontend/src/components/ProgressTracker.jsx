import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ProgressTracker.css';

function ProgressTracker({ jobId, onStatusUpdate, onError }) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/status/${jobId}`);
        setStatus(response.data.status);
        setProgress(response.data.progress || 0);
        
        if (response.data.error) {
          setError(response.data.error);
          onError(response.data.error);
        }
        
        onStatusUpdate(response.data.status);
        
        // Stop polling when completed or failed
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error checking status:', err);
      }
    }, 1000); // Check every second

    return () => clearInterval(interval);
  }, [jobId, onStatusUpdate, onError]);

  const getStatusMessage = () => {
    switch (status) {
      case 'pending':
        return 'Waiting to process...';
      case 'processing':
        return 'Processing your PDF...';
      case 'completed':
        return 'Processing complete!';
      case 'failed':
        return 'Processing failed';
      default:
        return 'Unknown status';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'processing':
        return '⚙️';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '❓';
    }
  };

  return (
    <div className="progress-tracker">
      <div className="tracker-card">
        <div className="status-header">
          <span className="status-icon">{getStatusIcon()}</span>
          <h2 className="status-message">{getStatusMessage()}</h2>
        </div>

        <div className="progress-bar-container">
          <div className="progress-bar-background">
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="progress-text">{progress}% Complete</p>
        </div>

        {error && (
          <div className="error-box">
            <p className="error-title">Error occurred:</p>
            <p className="error-details">{error}</p>
          </div>
        )}

        <div className="status-details">
          <p className="job-id">Job ID: <code>{jobId}</code></p>
        </div>

        {status === 'processing' && (
          <div className="processing-steps">
            <div className="step">
              <span className={`step-icon ${progress > 10 ? 'complete' : ''}`}>1</span>
              <span>Chunking PDF</span>
            </div>
            <div className="step">
              <span className={`step-icon ${progress > 40 ? 'complete' : ''}`}>2</span>
              <span>Extracting Text & OCR</span>
            </div>
            <div className="step">
              <span className={`step-icon ${progress > 75 ? 'complete' : ''}`}>3</span>
              <span>Processing with Claude</span>
            </div>
            <div className="step">
              <span className={`step-icon ${progress > 90 ? 'complete' : ''}`}>4</span>
              <span>Generating Excel</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProgressTracker;
