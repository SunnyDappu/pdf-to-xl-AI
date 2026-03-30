import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import ProgressTracker from './components/ProgressTracker';
import ResultDisplay from './components/ResultDisplay';
import './App.css';

function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = (newJobId) => {
    setJobId(newJobId);
    setStatus('pending');
    setError(null);
  };

  const handleStatusUpdate = (newStatus) => {
    setStatus(newStatus);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
  };

  const handleReset = () => {
    setJobId(null);
    setStatus(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📄→📊 PDF-to-Excel AI Extraction Bot</h1>
        <p className="subtitle">Upload PDFs, get structured Excel files instantly</p>
      </header>

      <main className="app-main">
        {!jobId ? (
          <UploadForm onUpload={handleUpload} />
        ) : (
          <div className="processing-container">
            <ProgressTracker 
              jobId={jobId}
              onStatusUpdate={handleStatusUpdate}
              onError={handleError}
            />
            {status === 'completed' && (
              <ResultDisplay jobId={jobId} onReset={handleReset} />
            )}
          </div>
        )}

        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={handleReset} className="btn-secondary">Clear</button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
