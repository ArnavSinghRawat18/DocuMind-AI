/**
 * frontend/src/services/api.js
 * API client for DocuMind AI frontend
 * Handles communication with the Node.js orchestrator backend
 */

import axios from 'axios';

// Base URL from environment or fallback to localhost
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3000';

/**
 * Pre-configured axios instance with defaults
 */
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

/**
 * Extracts a user-friendly error message from axios errors
 * Designed to NEVER crash regardless of error structure
 * 
 * @param {Error} err - The error object (axios or generic)
 * @returns {{ message: string, status: number | null }}
 */
function extractError(err) {
  try {
    // Network error (no response received)
    if (err.code === 'ECONNABORTED') {
      return {
        message: 'Request timed out. Please check your connection and try again.',
        status: null
      };
    }

    // No response from server (network issue)
    if (!err.response) {
      return {
        message: err.message || 'Unable to connect to the server. Please try again later.',
        status: null
      };
    }

    // Server responded with an error
    const { status, data } = err.response;

    // Try to extract message from various response formats
    const message = 
      data?.error ||
      data?.message ||
      data?.detail ||
      (typeof data === 'string' ? data : null) ||
      `Request failed with status ${status}`;

    return { message, status };

  } catch (extractionError) {
    // Fallback if extraction itself fails
    console.error('[api] Error extraction failed:', extractionError);
    return {
      message: 'An unexpected error occurred. Please try again.',
      status: null
    };
  }
}

/**
 * Starts a repository ingestion job
 * 
 * @param {string} repoUrl - The GitHub repository URL to ingest
 * @returns {Promise<string>} The job ID on success
 * @throws {{ message: string, status: number | null }} Structured error on failure
 */
export async function startIngest(repoUrl) {
  try {
    const response = await apiClient.post('/ingest', { repoUrl });

    // Validate response
    if (response.data?.success && response.data?.jobId) {
      return response.data.jobId;
    }

    // Unexpected response format
    throw new Error('Invalid response from server');

  } catch (err) {
    // If it's already a structured error, rethrow
    if (err.message && err.status !== undefined) {
      throw err;
    }

    // Extract and throw structured error
    const { message, status } = extractError(err);
    throw { message, status };
  }
}

/**
 * Retrieves the status of an ingestion job
 * 
 * @param {string} jobId - The job ID to query
 * @returns {Promise<Object>} The job document with status, progress, etc.
 * @throws {{ message: string, status: number | null }} Structured error on failure
 */
export async function getJobStatus(jobId) {
  try {
    const response = await apiClient.get(`/status/${jobId}`);

    return response.data;

  } catch (err) {
    const { message, status } = extractError(err);

    // Handle 404 specifically
    if (status === 404) {
      throw {
        message: `Job "${jobId}" not found. It may have expired or never existed.`,
        status: 404
      };
    }

    throw { message, status };
  }
}

/**
 * Health check for the backend API
 * 
 * @returns {Promise<boolean>} True if backend is healthy
 */
export async function checkHealth() {
  try {
    const response = await apiClient.get('/health');
    return response.data?.status === 'ok';
  } catch {
    return false;
  }
}

/**
 * Generates documentation using AI
 * 
 * @param {string} prompt - The user's prompt/question
 * @param {string} jobId - The job ID for context (codebase)
 * @param {string} [model='llama3-70b'] - AI model to use
 * @returns {Promise<{ title: string, content: string, chunksUsed: Array }>} Generated doc
 * @throws {{ message: string, status: number | null }} Structured error on failure
 */
export async function generateDoc(prompt, jobId, model = 'llama3-70b') {
  try {
    // Validate inputs
    if (!prompt || !prompt.trim()) {
      throw { message: 'Prompt is required', status: null };
    }

    if (!jobId) {
      throw { message: 'Job ID is required for context', status: null };
    }

    const response = await apiClient.post('/generate', {
      prompt: prompt.trim(),
      jobId,
      model
    }, {
      // Longer timeout for AI generation
      timeout: 60000 // 60 seconds
    });

    // Validate response
    if (!response.data) {
      throw new Error('Empty response from server');
    }

    // Return the generated document
    return {
      title: response.data.title || 'Generated Documentation',
      content: response.data.content || '',
      chunksUsed: response.data.chunksUsed || response.data.chunks_used || [],
      raw_url: response.data.raw_url || null,
      generatedAt: new Date().toISOString()
    };

  } catch (err) {
    // If it's already a structured error, rethrow
    if (err.message && err.status !== undefined) {
      throw err;
    }

    const { message, status } = extractError(err);

    // Handle specific error codes
    if (status === 404) {
      throw {
        message: 'Job not found. The codebase may have expired.',
        status: 404
      };
    }

    if (status === 429) {
      throw {
        message: 'Rate limit exceeded. Please wait a moment and try again.',
        status: 429
      };
    }

    throw { message, status };
  }
}

// Export the helper for testing purposes
export { extractError };

// Export the axios instance for advanced use cases
export { apiClient };
