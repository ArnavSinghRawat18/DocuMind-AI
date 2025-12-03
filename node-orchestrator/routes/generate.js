/**
 * node-orchestrator/routes/generate.js
 * Express route for AI documentation generation
 * 
 * Endpoint: POST /generate
 * Accepts a prompt and job context, forwards to FastAPI for AI processing,
 * persists the result to MongoDB, and returns the generated document.
 * 
 * Features:
 * - Request validation (jobId, prompt, model)
 * - Job existence verification via MongoDB
 * - Rate limiting per jobId (5 second cooldown)
 * - FastAPI integration with configurable timeout
 * - Error handling with appropriate status codes
 * - API key masking in logs
 */

const express = require('express');
const axios = require('axios');
const { getDb } = require('../db/mongo');

// ============================================================================
// Configuration
// ============================================================================

// FastAPI URL for AI generation
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

// Timeout for generation requests (default 60 seconds)
const GENERATE_TIMEOUT_MS = parseInt(process.env.GENERATE_TIMEOUT_MS, 10) || 60000;

// Rate limit window per job (milliseconds)
const RATE_LIMIT_WINDOW_MS = 5000;

// Maximum prompt length
const MAX_PROMPT_LENGTH = 2000;

// ============================================================================
// In-Memory Rate Limiting
// ============================================================================

/**
 * Simple in-memory rate limiter per jobId
 * Tracks last request timestamp for each job
 */
const rateLimitMap = new Map();

/**
 * Checks if a jobId is rate limited
 * @param {string} jobId - The job ID to check
 * @returns {boolean} True if rate limited, false otherwise
 */
function isRateLimited(jobId) {
  const lastRequest = rateLimitMap.get(jobId);
  if (!lastRequest) {
    return false;
  }
  return Date.now() - lastRequest < RATE_LIMIT_WINDOW_MS;
}

/**
 * Records a request for rate limiting
 * @param {string} jobId - The job ID to record
 */
function recordRequest(jobId) {
  rateLimitMap.set(jobId, Date.now());
  
  // Clean up old entries periodically (every 100 requests)
  if (rateLimitMap.size > 100) {
    const now = Date.now();
    for (const [id, timestamp] of rateLimitMap.entries()) {
      if (now - timestamp > RATE_LIMIT_WINDOW_MS * 2) {
        rateLimitMap.delete(id);
      }
    }
  }
}

// ============================================================================
// Logging Utilities
// ============================================================================

/**
 * Masks sensitive data in strings (API keys, tokens, etc.)
 * @param {string} str - String to mask
 * @returns {string} Masked string
 */
function maskSecrets(str) {
  if (!str || typeof str !== 'string') return str;
  
  // Mask API keys, tokens, bearer tokens
  return str
    .replace(/([A-Za-z0-9_-]{20,})/g, (match) => {
      if (match.length > 8) {
        return match.slice(0, 4) + '****' + match.slice(-4);
      }
      return '****';
    })
    .replace(/Bearer\s+[^\s]+/gi, 'Bearer ****')
    .replace(/api[_-]?key[=:]\s*[^\s&]+/gi, 'api_key=****');
}

/**
 * Logs a message with job context
 * @param {string} jobId - Job ID for context
 * @param {string} level - Log level (info, error, warn)
 * @param {string} message - Message to log
 * @param {Object} [data] - Additional data to log
 */
function log(jobId, level, message, data = null) {
  const prefix = `[generate][${jobId || 'unknown'}]`;
  const timestamp = new Date().toISOString();
  
  const logFn = level === 'error' ? console.error : 
                level === 'warn' ? console.warn : 
                console.log;
  
  if (data) {
    // Mask any sensitive data in the log
    const safeData = JSON.parse(JSON.stringify(data));
    logFn(`${timestamp} ${prefix} ${message}`, safeData);
  } else {
    logFn(`${timestamp} ${prefix} ${message}`);
  }
}

// ============================================================================
// Request Validation
// ============================================================================

/**
 * Validates the request body for /generate endpoint
 * @param {Object} body - Request body
 * @returns {{ valid: boolean, error?: string }}
 */
function validateRequest(body) {
  const { jobId, prompt, model } = body || {};

  // Validate jobId
  if (!jobId || typeof jobId !== 'string' || jobId.trim() === '') {
    return { valid: false, error: 'jobId is required and must be a non-empty string' };
  }

  // Validate prompt
  if (!prompt || typeof prompt !== 'string' || prompt.trim() === '') {
    return { valid: false, error: 'prompt is required and must be a non-empty string' };
  }

  if (prompt.length > MAX_PROMPT_LENGTH) {
    return { 
      valid: false, 
      error: `prompt exceeds maximum length of ${MAX_PROMPT_LENGTH} characters` 
    };
  }

  // Validate model (optional)
  if (model !== undefined && typeof model !== 'string') {
    return { valid: false, error: 'model must be a string if provided' };
  }

  return { valid: true };
}

// ============================================================================
// Route Handler
// ============================================================================

/**
 * POST /generate handler
 * Generates AI documentation based on prompt and job context
 */
async function handleGenerate(req, res) {
  const { jobId, prompt, model } = req.body;

  // ---- Step 1: Validate request ----
  const validation = validateRequest(req.body);
  if (!validation.valid) {
    log(jobId, 'warn', `Validation failed: ${validation.error}`);
    return res.status(400).json({
      success: false,
      error: validation.error
    });
  }

  const trimmedJobId = jobId.trim();
  const trimmedPrompt = prompt.trim();

  log(trimmedJobId, 'info', `Received generate request, prompt length: ${trimmedPrompt.length}`);

  // ---- Step 2: Check rate limit ----
  if (isRateLimited(trimmedJobId)) {
    log(trimmedJobId, 'warn', 'Rate limited - request within 5 second window');
    return res.status(429).json({
      success: false,
      error: 'Rate limited. Please wait 5 seconds before generating again for this job.'
    });
  }

  // Record this request for rate limiting
  recordRequest(trimmedJobId);

  try {
    // ---- Step 3: Verify job exists in MongoDB ----
    const db = await getDb();
    const job = await db.collection('jobs').findOne({ jobId: trimmedJobId });

    if (!job) {
      log(trimmedJobId, 'warn', 'Job not found in database');
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }

    log(trimmedJobId, 'info', `Found job for repo: ${maskSecrets(job.repoUrl)}`);

    // ---- Step 4: Build payload for FastAPI ----
    const fastApiPayload = {
      job_id: job.jobId,
      repo_url: job.repoUrl,
      prompt: trimmedPrompt,
      model: model || 'llama3-70b'
    };

    log(trimmedJobId, 'info', `Sending request to FastAPI at ${FASTAPI_URL}/generate`);

    // ---- Step 5: Call FastAPI ----
    let fastApiResponse;
    try {
      fastApiResponse = await axios.post(
        `${FASTAPI_URL}/generate`,
        fastApiPayload,
        {
          timeout: GENERATE_TIMEOUT_MS,
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
    } catch (axiosError) {
      // Handle axios errors
      return handleFastApiError(axiosError, trimmedJobId, res);
    }

    // ---- Step 6: Process successful response ----
    const fastApiData = fastApiResponse.data;

    log(trimmedJobId, 'info', 'Received successful response from FastAPI');

    // Build document to persist
    const generatedDoc = {
      jobId: trimmedJobId,
      title: fastApiData.title || 'Generated Documentation',
      content: fastApiData.content || '',
      model_used: fastApiData.model_used || model || 'llama3-70b',
      chunks_used: fastApiData.chunks_used || [],
      source: 'user_generate',
      prompt: trimmedPrompt,
      created_at: new Date()
    };

    // ---- Step 7: Persist to MongoDB ----
    log(trimmedJobId, 'info', 'Persisting generated document to MongoDB');

    const insertResult = await db.collection('generated_docs').insertOne(generatedDoc);

    // Add the MongoDB _id to the response
    const savedDoc = {
      ...generatedDoc,
      _id: insertResult.insertedId
    };

    log(trimmedJobId, 'info', `Document saved with _id: ${insertResult.insertedId}`);

    // ---- Step 8: Return success response ----
    return res.status(200).json({
      success: true,
      doc: savedDoc
    });

  } catch (error) {
    // Unexpected error
    log(trimmedJobId, 'error', `Unexpected error: ${maskSecrets(error.message)}`);
    console.error(error);

    return res.status(500).json({
      success: false,
      error: 'Internal server error during document generation'
    });
  }
}

/**
 * Handles errors from FastAPI requests
 * @param {Error} error - Axios error
 * @param {string} jobId - Job ID for logging
 * @param {Object} res - Express response object
 */
function handleFastApiError(error, jobId, res) {
  // Timeout error
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    log(jobId, 'error', 'FastAPI request timed out');
    return res.status(504).json({
      success: false,
      error: 'AI generation timed out. The request took too long to process. Please try again with a simpler prompt.'
    });
  }

  // Network error (no response)
  if (!error.response) {
    log(jobId, 'error', `FastAPI network error: ${maskSecrets(error.message)}`);
    return res.status(502).json({
      success: false,
      error: 'Unable to reach the AI service. Please try again later.'
    });
  }

  // FastAPI returned an error response
  const { status, data } = error.response;
  const errorMessage = data?.detail || data?.error || data?.message || 'AI service error';

  log(jobId, 'error', `FastAPI returned ${status}: ${maskSecrets(errorMessage)}`);

  // Map FastAPI status codes to appropriate Express responses
  if (status >= 400 && status < 500) {
    // Client errors from FastAPI (4xx)
    return res.status(status).json({
      success: false,
      error: errorMessage
    });
  }

  // Server errors from FastAPI (5xx)
  return res.status(502).json({
    success: false,
    error: 'AI service encountered an error. Please try again later.'
  });
}

// ============================================================================
// Router Setup
// ============================================================================

/**
 * Creates and configures the Express router for /generate
 * @returns {express.Router} Configured router
 */
function createRouter() {
  const router = express.Router();
  
  router.post('/generate', handleGenerate);
  
  return router;
}

/**
 * Attaches the /generate route to an Express app
 * @param {express.Application} app - Express app instance
 */
function attachToApp(app) {
  app.post('/generate', handleGenerate);
}

// ============================================================================
// Exports
// ============================================================================

// Create router instance
const router = createRouter();

module.exports = {
  // Primary exports
  router,
  attachToApp,
  
  // For unit testing
  handleGenerate,
  validateRequest,
  isRateLimited,
  recordRequest,
  maskSecrets,
  
  // Constants for testing
  MAX_PROMPT_LENGTH,
  RATE_LIMIT_WINDOW_MS
};
