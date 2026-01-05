/**
 * DocuMind AI — Frontend
 * Single-file polished UI for AI-powered documentation generation
 * 
 * Features:
 * - GitHub Repository URL input
 * - One-click documentation generation (ingest + generate)
 * - Loading state with progress messages
 * - Markdown rendering
 * - README.md download
 * - Error handling
 */

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

/* =============================================================================
   STYLES (Embedded CSS-in-JS)
============================================================================= */

const styles = {
  // Global container
  app: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    color: '#e4e4e4',
    padding: '0',
    margin: '0',
  },

  // Header
  header: {
    textAlign: 'center',
    padding: '40px 20px 30px',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
  },
  title: {
    fontSize: '2.8rem',
    fontWeight: '700',
    margin: '0 0 8px 0',
    background: 'linear-gradient(90deg, #00d4ff, #7c3aed, #f472b6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  subtitle: {
    fontSize: '1.1rem',
    color: '#94a3b8',
    margin: '0',
    fontWeight: '400',
  },

  // Main container
  main: {
    maxWidth: '900px',
    margin: '0 auto',
    padding: '30px 20px',
  },

  // Card component
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '28px',
    marginBottom: '24px',
    backdropFilter: 'blur(10px)',
  },
  cardTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    marginBottom: '20px',
    color: '#f1f5f9',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },

  // Input section
  inputGroup: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  input: {
    flex: '1',
    minWidth: '280px',
    padding: '14px 18px',
    fontSize: '1rem',
    border: '2px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '10px',
    background: 'rgba(0, 0, 0, 0.3)',
    color: '#fff',
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  },
  inputFocus: {
    borderColor: '#00d4ff',
    boxShadow: '0 0 0 3px rgba(0, 212, 255, 0.2)',
  },

  // Buttons
  button: {
    padding: '14px 28px',
    fontSize: '1rem',
    fontWeight: '600',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  buttonPrimary: {
    background: 'linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)',
    color: '#fff',
  },
  buttonPrimaryHover: {
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 25px rgba(0, 212, 255, 0.3)',
  },
  buttonDisabled: {
    background: '#374151',
    color: '#6b7280',
    cursor: 'not-allowed',
    transform: 'none',
    boxShadow: 'none',
  },
  buttonDownload: {
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    color: '#fff',
    marginTop: '16px',
  },

  // Loading state
  loadingContainer: {
    textAlign: 'center',
    padding: '50px 20px',
  },
  spinner: {
    width: '50px',
    height: '50px',
    border: '4px solid rgba(255, 255, 255, 0.1)',
    borderTopColor: '#00d4ff',
    borderRadius: '50%',
    margin: '0 auto 20px',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    fontSize: '1.1rem',
    color: '#94a3b8',
  },

  // Error state
  errorBox: {
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    borderRadius: '10px',
    padding: '16px 20px',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  errorIcon: {
    fontSize: '1.5rem',
  },
  errorText: {
    color: '#fca5a5',
    margin: '0',
    fontSize: '0.95rem',
  },

  // Documentation viewer
  docViewer: {
    background: 'rgba(0, 0, 0, 0.4)',
    borderRadius: '12px',
    padding: '24px 28px',
    maxHeight: '500px',
    overflowY: 'auto',
    border: '1px solid rgba(255, 255, 255, 0.08)',
  },
  markdown: {
    lineHeight: '1.7',
    color: '#e2e8f0',
  },

  // Footer
  footer: {
    textAlign: 'center',
    padding: '30px 20px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    marginTop: '40px',
    color: '#64748b',
    fontSize: '0.9rem',
  },

  // Success badge
  successBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    background: 'rgba(16, 185, 129, 0.2)',
    color: '#34d399',
    padding: '6px 12px',
    borderRadius: '20px',
    fontSize: '0.85rem',
    fontWeight: '500',
    marginBottom: '16px',
  },

  // Stats row
  statsRow: {
    display: 'flex',
    gap: '20px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  statItem: {
    background: 'rgba(255, 255, 255, 0.05)',
    padding: '10px 16px',
    borderRadius: '8px',
    fontSize: '0.85rem',
    color: '#94a3b8',
  },
  statValue: {
    color: '#00d4ff',
    fontWeight: '600',
  },
};

/* =============================================================================
   CSS KEYFRAMES (Injected via style tag)
============================================================================= */

const keyframesStyle = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  /* Markdown Styles */
  .markdown-content h1 {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 24px 0 16px;
    color: #f1f5f9;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
  }
  .markdown-content h2 {
    font-size: 1.4rem;
    font-weight: 600;
    margin: 20px 0 12px;
    color: #e2e8f0;
  }
  .markdown-content h3 {
    font-size: 1.15rem;
    font-weight: 600;
    margin: 16px 0 10px;
    color: #cbd5e1;
  }
  .markdown-content p {
    margin: 12px 0;
    color: #94a3b8;
  }
  .markdown-content ul, .markdown-content ol {
    margin: 12px 0;
    padding-left: 24px;
    color: #94a3b8;
  }
  .markdown-content li {
    margin: 6px 0;
  }
  .markdown-content code {
    background: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
  }
  .markdown-content pre {
    background: rgba(0, 0, 0, 0.5);
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    border: 1px solid rgba(255,255,255,0.1);
  }
  .markdown-content pre code {
    background: none;
    padding: 0;
    color: #e2e8f0;
  }
  .markdown-content strong {
    color: #f1f5f9;
    font-weight: 600;
  }
  .markdown-content a {
    color: #00d4ff;
    text-decoration: none;
  }
  .markdown-content a:hover {
    text-decoration: underline;
  }
  
  /* Scrollbar */
  .doc-viewer::-webkit-scrollbar {
    width: 8px;
  }
  .doc-viewer::-webkit-scrollbar-track {
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
  }
  .doc-viewer::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.2);
    border-radius: 4px;
  }
  .doc-viewer::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.3);
  }
  
  /* Input placeholder */
  input::placeholder {
    color: #64748b;
  }
`;

/* =============================================================================
   MAIN APP COMPONENT
============================================================================= */

export default function App() {
  // ─────────────────────────────────────────────────────────────────────────
  // STATE
  // ─────────────────────────────────────────────────────────────────────────
  const [repoUrl, setRepoUrl] = useState('');           // User-visible input
  const [docType, setDocType] = useState('README');     // README or DETAILED
  const [jobId, setJobId] = useState('');               // Internal only, never shown
  const [isLoading, setIsLoading] = useState(false);    // Covers ingest + generate
  const [statusMessage, setStatusMessage] = useState(''); // Progress messages
  const [docsContent, setDocsContent] = useState('');
  const [error, setError] = useState('');
  const [generationTime, setGenerationTime] = useState(null);
  const [inputFocused, setInputFocused] = useState(false);
  const [buttonHovered, setButtonHovered] = useState(false);
  
  // Backend status check
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking', 'online', 'offline', 'ready'
  const [backendWaitTime, setBackendWaitTime] = useState(30);

  // ─────────────────────────────────────────────────────────────────────────
  // BACKEND HEALTH CHECK (for Render cold start)
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(5000) // 5 second timeout
        });
        if (response.ok) {
          setBackendStatus('online');
          // Auto-hide the online banner after 3 seconds
          setTimeout(() => setBackendStatus('ready'), 3000);
        } else {
          setBackendStatus('offline');
        }
      } catch (err) {
        setBackendStatus('offline');
      }
    };

    // Initial check
    checkBackend();

    // If offline, retry every 5 seconds and countdown
    let retryInterval;
    let countdownInterval;
    
    if (backendStatus === 'checking' || backendStatus === 'offline') {
      retryInterval = setInterval(() => {
        checkBackend();
      }, 5000);
      
      countdownInterval = setInterval(() => {
        setBackendWaitTime(prev => (prev > 0 ? prev - 1 : 30));
      }, 1000);
    }

    return () => {
      clearInterval(retryInterval);
      clearInterval(countdownInterval);
    };
  }, [backendStatus]);

  // ─────────────────────────────────────────────────────────────────────────
  // GITHUB URL VALIDATION
  // ─────────────────────────────────────────────────────────────────────────
  const isValidGitHubUrl = (url) => {
    const pattern = /^https?:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+\/?$/i;
    return pattern.test(url.trim());
  };

  // ─────────────────────────────────────────────────────────────────────────
  // MAIN HANDLER: INGEST + GENERATE
  // ─────────────────────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    // Validate GitHub URL
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL');
      return;
    }

    if (!isValidGitHubUrl(repoUrl)) {
      setError('Please enter a valid GitHub URL (e.g., https://github.com/owner/repo)');
      return;
    }

    // Reset state
    setError('');
    setDocsContent('');
    setJobId('');
    setIsLoading(true);
    setGenerationTime(null);

    const startTime = Date.now();

    try {
      // ═══════════════════════════════════════════════════════════════════
      // STEP 1: INGEST REPOSITORY
      // ═══════════════════════════════════════════════════════════════════
      setStatusMessage('📥 Ingesting repository…');

      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const ingestResponse = await fetch(`${API_BASE}/api/v1/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() })
      });

      const ingestData = await ingestResponse.json();

      if (!ingestResponse.ok) {
        throw new Error(ingestData.detail || ingestData.message || 'Failed to ingest repository');
      }

      const receivedJobId = ingestData.job_id;
      if (!receivedJobId) {
        throw new Error('No job ID received from server');
      }

      setJobId(receivedJobId); // Store internally

      // ═══════════════════════════════════════════════════════════════════
      // STEP 2: ANALYZE CODEBASE
      // ═══════════════════════════════════════════════════════════════════
      setStatusMessage('🔍 Analyzing codebase…');
      
      // Small delay for UX (shows progress)
      await new Promise(resolve => setTimeout(resolve, 500));

      // ═══════════════════════════════════════════════════════════════════
      // STEP 3: GENERATE DOCUMENTATION
      // ═══════════════════════════════════════════════════════════════════
      const statusMsg = docType === 'DETAILED' 
        ? '🤖 Generating detailed documentation… (this may take 1-2 minutes)'
        : '🤖 Generating documentation with AI…';
      setStatusMessage(statusMsg);

      const generateResponse = await fetch(`${API_BASE}/api/v1/generate/docs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: receivedJobId,
          doc_type: docType
        })
      });

      const generateData = await generateResponse.json();

      if (!generateResponse.ok) {
        throw new Error(generateData.detail || generateData.message || 'Failed to generate documentation');
      }

      // Handle response - backend returns { answer: "...", status: "success", ... }
      const content = generateData.answer || generateData.content || '';
      
      if (!content) {
        throw new Error('No documentation content received');
      }

      setDocsContent(content);
      setGenerationTime(((Date.now() - startTime) / 1000).toFixed(2));
      setStatusMessage('');

    } catch (err) {
      console.error('Generation error:', err);
      // Handle different error formats
      let errorMessage = 'Failed to connect to backend. Is the server running?';
      if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'object') {
        errorMessage = JSON.stringify(err);
      }
      setError(errorMessage);
      setDocsContent('');
      setStatusMessage('');
    } finally {
      setIsLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // DOWNLOAD HANDLER
  // ─────────────────────────────────────────────────────────────────────────
  const handleDownload = () => {
    if (!docsContent) return;

    const blob = new Blob([docsContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'README.md';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // KEYBOARD HANDLER
  // ─────────────────────────────────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isLoading && repoUrl.trim()) {
      handleGenerate();
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────
  const isBackendReady = backendStatus === 'online' || backendStatus === 'ready';
  const isButtonDisabled = !repoUrl.trim() || isLoading || !isBackendReady;

  return (
    <div style={styles.app}>
      {/* Inject keyframes */}
      <style>{keyframesStyle}</style>

      {/* ═══════════════════════════════════════════════════════════════════
          HEADER
      ═══════════════════════════════════════════════════════════════════ */}
      <header style={styles.header}>
        <h1 style={styles.title}>🧠 DocuMind AI</h1>
        <p style={styles.subtitle}>AI-Powered Code Documentation Generator</p>
      </header>

      {/* ═══════════════════════════════════════════════════════════════════
          BACKEND STATUS BANNER
      ═══════════════════════════════════════════════════════════════════ */}
      {(backendStatus === 'checking' || backendStatus === 'offline') && (
        <div style={{
          background: backendStatus === 'checking' 
            ? 'linear-gradient(90deg, #f59e0b, #d97706)' 
            : 'linear-gradient(90deg, #ef4444, #dc2626)',
          padding: '12px 20px',
          textAlign: 'center',
          color: '#fff',
          fontWeight: '500',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          fontSize: '0.95rem',
        }}>
          <span style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            border: '2px solid #fff',
            borderTopColor: 'transparent',
            animation: 'spin 1s linear infinite',
          }} />
          <span>
            {backendStatus === 'checking' 
              ? '🔄 Connecting to backend server...' 
              : `⏳ Backend server is waking up... Please wait ~${backendWaitTime}s (Free tier cold start)`
            }
          </span>
        </div>
      )}

      {/* Online status banner (shows briefly then fades) */}
      {backendStatus === 'online' && (
        <div style={{
          background: 'linear-gradient(90deg, #10b981, #059669)',
          padding: '10px 20px',
          textAlign: 'center',
          color: '#fff',
          fontWeight: '500',
          fontSize: '0.9rem',
        }}>
          ✅ Backend server is online and ready!
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN CONTENT
      ═══════════════════════════════════════════════════════════════════ */}
      <main style={styles.main}>
        
        {/* ─────────────────────────────────────────────────────────────────
            INPUT SECTION
        ───────────────────────────────────────────────────────────────── */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>
            <span>🔗</span> Generate Documentation
          </h2>
          
          <div style={styles.inputGroup}>
            <input
              type="text"
              placeholder="Paste GitHub Repository URL (e.g., https://github.com/owner/repo)"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onFocus={() => setInputFocused(true)}
              onBlur={() => setInputFocused(false)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              style={{
                ...styles.input,
                ...(inputFocused ? styles.inputFocus : {}),
                opacity: isLoading ? 0.6 : 1,
              }}
            />
          </div>

          {/* Documentation Type Selector */}
          <div style={{ marginTop: '16px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Documentation Type:</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setDocType('README')}
                disabled={isLoading}
                style={{
                  padding: '10px 20px',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  border: docType === 'README' ? '2px solid #00d4ff' : '2px solid rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  background: docType === 'README' ? 'rgba(0, 212, 255, 0.15)' : 'rgba(0,0,0,0.3)',
                  color: docType === 'README' ? '#00d4ff' : '#94a3b8',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                📄 Quick README
              </button>
              <button
                onClick={() => setDocType('DETAILED')}
                disabled={isLoading}
                style={{
                  padding: '10px 20px',
                  fontSize: '0.9rem',
                  fontWeight: '500',
                  border: docType === 'DETAILED' ? '2px solid #f472b6' : '2px solid rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  background: docType === 'DETAILED' ? 'rgba(244, 114, 182, 0.15)' : 'rgba(0,0,0,0.3)',
                  color: docType === 'DETAILED' ? '#f472b6' : '#94a3b8',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                📚 Detailed (Examiner-Ready)
              </button>
            </div>
          </div>
          {docType === 'DETAILED' && (
            <p style={{ marginTop: '10px', fontSize: '0.85rem', color: '#f472b6', fontStyle: 'italic' }}>
              ⚠️ Detailed mode generates comprehensive, examiner-level documentation. Takes 1-2 minutes.
            </p>
          )}

          {/* Generate Button */}
          <div style={{ marginTop: '20px' }}>
            <button
              onClick={handleGenerate}
              disabled={isButtonDisabled}
              onMouseEnter={() => setButtonHovered(true)}
              onMouseLeave={() => setButtonHovered(false)}
              style={{
                ...styles.button,
                ...styles.buttonPrimary,
                ...(isButtonDisabled ? styles.buttonDisabled : {}),
                ...(!isButtonDisabled && buttonHovered ? styles.buttonPrimaryHover : {}),
                width: '100%',
                justifyContent: 'center',
              }}
            >
              {isLoading ? (
                <>
                  <span style={{ 
                    width: '18px', 
                    height: '18px', 
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTopColor: '#fff',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                    display: 'inline-block',
                  }} />
                  Processing...
                </>
              ) : (
                <>
                  <span>✨</span>
                  Generate {docType === 'DETAILED' ? 'Detailed ' : ''}Documentation
                </>
              )}
            </button>
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────────
            ERROR STATE
        ───────────────────────────────────────────────────────────────── */}
        {error && (
          <div style={styles.errorBox}>
            <span style={styles.errorIcon}>⚠️</span>
            <p style={styles.errorText}>{error}</p>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────────
            LOADING STATE
        ───────────────────────────────────────────────────────────────── */}
        {isLoading && (
          <div style={styles.card}>
            <div style={styles.loadingContainer}>
              <div style={styles.spinner} />
              <p style={styles.loadingText}>
                {statusMessage || '🤖 Processing…'}
              </p>
              <p style={{ ...styles.loadingText, fontSize: '0.9rem', marginTop: '8px' }}>
                This typically takes 15-30 seconds
              </p>
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────────
            DOCUMENTATION VIEWER
        ───────────────────────────────────────────────────────────────── */}
        {docsContent && !isLoading && (
          <div style={styles.card}>
            <h2 style={styles.cardTitle}>
              <span>📄</span> Generated Documentation
            </h2>

            {/* Success badge + stats */}
            <div style={styles.successBadge}>
              <span>✓</span> Successfully Generated
            </div>

            {generationTime && (
              <div style={styles.statsRow}>
                <div style={styles.statItem}>
                  ⏱️ Time: <span style={styles.statValue}>{generationTime}s</span>
                </div>
                <div style={styles.statItem}>
                  📝 Type: <span style={styles.statValue}>README.md</span>
                </div>
              </div>
            )}

            {/* Markdown content */}
            <div 
              className="doc-viewer" 
              style={styles.docViewer}
            >
              <div className="markdown-content" style={styles.markdown}>
                <ReactMarkdown>{docsContent}</ReactMarkdown>
              </div>
            </div>

            {/* Download button */}
            <button
              onClick={handleDownload}
              style={{
                ...styles.button,
                ...styles.buttonDownload,
              }}
            >
              <span>📥</span>
              Download README.md
            </button>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────────
            EMPTY STATE (INITIAL)
        ───────────────────────────────────────────────────────────────── */}
        {!docsContent && !isLoading && !error && (
          <div style={{ ...styles.card, textAlign: 'center', padding: '50px 28px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📚</div>
            <h3 style={{ 
              color: '#94a3b8', 
              fontWeight: '500', 
              margin: '0 0 8px',
              fontSize: '1.1rem'
            }}>
              Ready to Generate Documentation
            </h3>
            <p style={{ color: '#64748b', margin: '0', fontSize: '0.95rem' }}>
              Paste a GitHub repository URL above and click "Generate Documentation"
            </p>
          </div>
        )}

      </main>

      {/* ═══════════════════════════════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════════════════════════════ */}
      <footer style={styles.footer}>
        <p style={{ margin: '0' }}>
          DocuMind AI — Built with React + FastAPI + Ollama (qwen2.5:3b)
        </p>
        <p style={{ margin: '8px 0 0', fontSize: '0.85rem' }}>
          © 2025 — AI-Powered Code Documentation
        </p>
      </footer>
    </div>
  );
}
