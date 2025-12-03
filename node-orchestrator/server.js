/**
 * node-orchestrator/server.js
 * Express-based API server for DocuMind AI orchestrator
 * Handles ingestion requests, status queries, and AI documentation generation
 */

require('dotenv').config();

const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const { ingestRepository, getJobStatus } = require('./ingest');
const { connect } = require('./db/mongo');
const { attachToApp: attachGenerateRoute } = require('./routes/generate');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors());

/**
 * Validates a repository URL
 * @param {string} url - URL to validate
 * @returns {boolean} - True if valid
 */
function isValidRepoUrl(url) {
  if (!url || typeof url !== 'string') {
    return false;
  }
  return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * POST /ingest
 * Starts a new repository ingestion job
 */
app.post('/ingest', async (req, res) => {
  try {
    const { repoUrl } = req.body;

    // Validate repoUrl
    if (!isValidRepoUrl(repoUrl)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid repository URL. Must be a valid http:// or https:// URL'
      });
    }

    // Generate job ID
    const jobId = uuidv4();

    console.log(`[server] Starting ingestion job ${jobId} for repo: ${repoUrl}`);

    // Fire-and-forget: run ingestion in background
    ingestRepository(repoUrl, { jobId })
      .then(() => {
        console.log(`[server] Job ${jobId} completed successfully`);
      })
      .catch((error) => {
        console.error(`[server] Job ${jobId} failed:`, error.message);
      });

    // Respond immediately
    res.json({
      success: true,
      jobId
    });

  } catch (error) {
    console.error('[server] Error in /ingest:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
});

/**
 * GET /status/:jobId
 * Retrieves the status of a job
 */
app.get('/status/:jobId', async (req, res) => {
  try {
    const { jobId } = req.params;

    const job = await getJobStatus(jobId);

    res.json(job);

  } catch (error) {
    if (error.message.includes('not found')) {
      return res.status(404).json({
        success: false,
        error: `Job ${req.params.jobId} not found`
      });
    }

    console.error('[server] Error in /status:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
});

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Attach /generate route
attachGenerateRoute(app);

/**
 * Start the server
 */
async function startServer() {
  try {
    // Initialize MongoDB connection
    console.log('[server] Connecting to MongoDB...');
    await connect();
    console.log('[server] MongoDB connected successfully');

    // Start Express server
    app.listen(PORT, () => {
      console.log(`[server] DocuMind AI Orchestrator running on port ${PORT}`);
      console.log(`[server] Endpoints:`);
      console.log(`[server]   POST /ingest - Start ingestion`);
      console.log(`[server]   GET /status/:jobId - Get job status`);
      console.log(`[server]   POST /generate - Generate AI documentation`);
      console.log(`[server]   GET /health - Health check`);
    });

  } catch (error) {
    console.error('[server] Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer();
