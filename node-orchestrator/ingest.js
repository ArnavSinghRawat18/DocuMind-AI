/**
 * node-orchestrator/ingest.js
 * Production-ready ingestion pipeline for DocuMind AI
 * Handles Git repo cloning, file scanning, chunking, MongoDB persistence, and FastAPI integration
 * with robust batching, retries, and progress tracking.
 */

require('dotenv').config();

const gitClient = require('./git_client');
const fileWalker = require('./file_walker');
const chunker = require('./chunker');
const { getDb } = require('./db/mongo');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

// Configuration from environment variables
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '200', 10);
const BATCH_CONCURRENCY = parseInt(process.env.BATCH_CONCURRENCY || '2', 10);
const BATCH_RETRIES = parseInt(process.env.BATCH_RETRIES || '3', 10);
const BATCH_RETRY_BASE_MS = parseInt(process.env.BATCH_RETRY_BASE_MS || '1000', 10);

const MONGO_BATCH_SIZE = 500; // For insertMany operations
const HTTP_TIMEOUT_MS = 120000; // 120 seconds per request

/**
 * Validates a repository URL
 * @param {string} url - The repository URL to validate
 * @returns {boolean} - True if valid
 * @throws {Error} - If URL is invalid or suspicious
 */
function validateRepoUrl(url) {
  if (!url || typeof url !== 'string') {
    throw new Error('Repository URL must be a non-empty string');
  }

  // Basic URL format check
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    throw new Error('Repository URL must start with http:// or https://');
  }

  // Security: Block localhost, 127.0.0.1, file://, internal IPs
  const suspiciousPatterns = [
    /localhost/i,
    /127\.0\.0\.1/,
    /file:\/\//i,
    /^https?:\/\/10\./,
    /^https?:\/\/172\.(1[6-9]|2[0-9]|3[0-1])\./,
    /^https?:\/\/192\.168\./,
  ];

  for (const pattern of suspiciousPatterns) {
    if (pattern.test(url)) {
      throw new Error(`Repository URL contains suspicious or blocked pattern: ${url}`);
    }
  }

  return true;
}

/**
 * Masks secrets in text using simple regex patterns
 * @param {string} text - The text to sanitize
 * @returns {string} - Text with secrets masked
 */
function maskSecrets(text) {
  if (!text) return text;

  // AWS Access Key pattern
  text = text.replace(/AKIA[0-9A-Z]{16}/g, '[REDACTED_AWS_KEY]');
  
  // Generic private key pattern
  text = text.replace(/-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----/gi, '[REDACTED_PRIVATE_KEY]');
  
  // Generic secret/token patterns (loose match)
  text = text.replace(/["']?[a-z_]*(?:secret|token|password|key)["']?\s*[:=]\s*["']([^"'\s]{20,})["']/gi, (match, secret) => {
    return match.replace(secret, '[REDACTED_SECRET]');
  });

  return text;
}

/**
 * Extracts repository name from URL
 * @param {string} repoUrl - Repository URL
 * @returns {string} - Repository name
 */
function extractRepoName(repoUrl) {
  const match = repoUrl.match(/\/([^\/]+?)(?:\.git)?$/);
  return match ? match[1] : 'unknown';
}

/**
 * Updates job status in MongoDB
 * @param {Object} jobsCollection - MongoDB collection
 * @param {string} jobId - Job identifier
 * @param {string} status - New status
 * @param {number} progress - Progress percentage (0-100)
 * @param {Object} additionalData - Additional fields to update
 */
async function updateJobStatus(jobsCollection, jobId, status, progress, additionalData = {}) {
  await jobsCollection.updateOne(
    { jobId },
    { 
      $set: { 
        status,
        progress,
        updatedAt: new Date(),
        ...additionalData
      } 
    }
  );
  console.log(`[ingest][${jobId}] Status: ${status} | Progress: ${progress}%`);
}

/**
 * Inserts chunks into MongoDB in batches
 * @param {Object} chunksCollection - MongoDB collection
 * @param {Array} chunkDocs - Array of chunk documents
 * @param {string} jobId - Job identifier
 */
async function insertChunksInBatches(chunksCollection, chunkDocs, jobId) {
  if (chunkDocs.length === 0) return;

  console.log(`[ingest][${jobId}] Inserting ${chunkDocs.length} chunks into MongoDB in batches of ${MONGO_BATCH_SIZE}`);

  for (let i = 0; i < chunkDocs.length; i += MONGO_BATCH_SIZE) {
    const batch = chunkDocs.slice(i, i + MONGO_BATCH_SIZE);
    try {
      await chunksCollection.insertMany(batch, { ordered: false });
      console.log(`[ingest][${jobId}] Inserted batch ${Math.floor(i / MONGO_BATCH_SIZE) + 1}/${Math.ceil(chunkDocs.length / MONGO_BATCH_SIZE)}`);
    } catch (error) {
      // Continue on duplicate key errors, but log other errors
      if (error.code !== 11000) {
        console.error(`[ingest][${jobId}] Batch insert error:`, error.message);
      }
    }
  }
}

/**
 * Posts a single batch to FastAPI with retry logic
 * @param {Array} batchChunks - Batch of chunks to send
 * @param {string} jobId - Job identifier
 * @param {string} repoUrl - Repository URL
 * @param {number} batchIndex - Batch number for logging
 * @returns {Promise<void>}
 */
async function postBatchWithRetry(batchChunks, jobId, repoUrl, batchIndex) {
  let lastError;

  for (let attempt = 0; attempt <= BATCH_RETRIES; attempt++) {
    try {
      const response = await axios.post(
        `${FASTAPI_URL}/ingest`,
        {
          job_id: jobId,
          repo_url: repoUrl,
          chunks: batchChunks
        },
        {
          timeout: HTTP_TIMEOUT_MS,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      if (response.status >= 200 && response.status < 300) {
        console.log(`[ingest][${jobId}] Batch ${batchIndex} uploaded successfully (${batchChunks.length} chunks)`);
        return;
      }

      throw new Error(`Unexpected status ${response.status}: ${JSON.stringify(response.data)}`);
    } catch (error) {
      lastError = error;
      
      if (attempt < BATCH_RETRIES) {
        const delay = BATCH_RETRY_BASE_MS * Math.pow(2, attempt);
        console.warn(`[ingest][${jobId}] Batch ${batchIndex} attempt ${attempt + 1} failed: ${error.message}. Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  // All retries exhausted
  const errorMsg = lastError.response 
    ? `HTTP ${lastError.response.status}: ${JSON.stringify(lastError.response.data)}`
    : lastError.message;
  throw new Error(`Batch ${batchIndex} failed after ${BATCH_RETRIES + 1} attempts: ${errorMsg}`);
}

/**
 * Posts chunks to FastAPI in batches with concurrency control
 * @param {Array} chunks - All chunks to upload
 * @param {string} jobId - Job identifier
 * @param {string} repoUrl - Repository URL
 * @param {Object} jobsCollection - MongoDB jobs collection
 * @returns {Promise<void>}
 */
async function postChunksInBatches(chunks, jobId, repoUrl, jobsCollection) {
  if (chunks.length === 0) return;

  // Mask secrets in chunk text before sending
  const sanitizedChunks = chunks.map(chunk => ({
    ...chunk,
    text: maskSecrets(chunk.text)
  }));

  const batches = [];
  for (let i = 0; i < sanitizedChunks.length; i += BATCH_SIZE) {
    batches.push(sanitizedChunks.slice(i, i + BATCH_SIZE));
  }

  console.log(`[ingest][${jobId}] Uploading ${sanitizedChunks.length} chunks in ${batches.length} batches (concurrency: ${BATCH_CONCURRENCY})`);

  const baseProgress = 75;
  const progressRange = 20; // 75 to 95

  // Process batches with concurrency control
  for (let i = 0; i < batches.length; i += BATCH_CONCURRENCY) {
    const batchPromises = [];
    
    for (let j = 0; j < BATCH_CONCURRENCY && i + j < batches.length; j++) {
      const batchIndex = i + j + 1;
      batchPromises.push(
        postBatchWithRetry(batches[i + j], jobId, repoUrl, batchIndex)
      );
    }

    await Promise.all(batchPromises);

    // Update progress
    const completedBatches = Math.min(i + BATCH_CONCURRENCY, batches.length);
    const progress = baseProgress + Math.floor((completedBatches / batches.length) * progressRange);
    await updateJobStatus(jobsCollection, jobId, 'uploading', progress);
  }

  console.log(`[ingest][${jobId}] All batches uploaded successfully`);
}

/**
 * Main ingestion function
 * @param {string} repoUrl - GitHub repository URL
 * @param {Object} options - Optional parameters
 * @param {string} options.jobId - Optional job ID (generated if not provided)
 * @param {string} options.startedBy - Optional user identifier
 * @returns {Promise<Object>} Job result with success, jobId, repoUrl, totalFiles, totalChunks
 */
async function ingestRepository(repoUrl, options = {}) {
  // Validate input
  validateRepoUrl(repoUrl);
  
  const jobId = options.jobId || uuidv4();
  const startedBy = options.startedBy || 'system';
  const repoName = extractRepoName(repoUrl);

  console.log(`[ingest][${jobId}] Starting ingestion for: ${repoUrl}`);

  const db = await getDb();
  const jobsCollection = db.collection('jobs');
  const chunksCollection = db.collection('chunks');

  let repoPath;

  try {
    // Create initial job entry
    await jobsCollection.insertOne({
      jobId,
      repoUrl,
      repoName,
      status: 'started',
      progress: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      meta: {
        startedBy
      }
    });

    // Step 1: Clone repository
    await updateJobStatus(jobsCollection, jobId, 'cloning', 5);
    repoPath = await gitClient.cloneRepository(repoUrl, jobId);
    console.log(`[ingest][${jobId}] Repository cloned to: ${repoPath}`);
    await updateJobStatus(jobsCollection, jobId, 'cloned', 10);

    // Step 2: Scan files
    await updateJobStatus(jobsCollection, jobId, 'scanning', 15);
    const files = await fileWalker.scanFiles(repoPath);
    console.log(`[ingest][${jobId}] Found ${files.length} files`);
    await updateJobStatus(jobsCollection, jobId, 'scanned', 25);

    // Step 3: Chunk code
    await updateJobStatus(jobsCollection, jobId, 'chunking', 30);
    const chunks = await chunker.chunkFiles(files, repoPath);
    console.log(`[ingest][${jobId}] Created ${chunks.length} chunks`);
    await updateJobStatus(jobsCollection, jobId, 'chunked', 60);

    // Step 4: Store chunks in MongoDB
    await updateJobStatus(jobsCollection, jobId, 'storing', 65);
    
    const chunkDocs = chunks.map(chunk => ({
      jobId,
      repoUrl,
      repoName,
      path: chunk.path,
      lang: chunk.lang,
      text: chunk.text,
      startChar: chunk.startChar,
      endChar: chunk.endChar,
      createdAt: new Date()
    }));
    
    await insertChunksInBatches(chunksCollection, chunkDocs, jobId);
    await updateJobStatus(jobsCollection, jobId, 'stored', 75);

    // Step 5: Upload chunks to FastAPI in batches
    await postChunksInBatches(chunks, jobId, repoUrl, jobsCollection);

    // Step 6: Mark job as completed
    await updateJobStatus(jobsCollection, jobId, 'completed', 100, {
      totalChunks: chunks.length,
      totalFiles: files.length,
      completedAt: new Date()
    });

    console.log(`[ingest][${jobId}] Ingestion completed successfully`);

    return {
      success: true,
      jobId,
      repoUrl,
      totalFiles: files.length,
      totalChunks: chunks.length
    };

  } catch (error) {
    console.error(`[ingest][${jobId}] Error during ingestion:`, error);
    
    // Truncate error stack for storage
    const errorStack = error.stack ? error.stack.substring(0, 2000) : '';
    
    // Update job status to failed
    await updateJobStatus(jobsCollection, jobId, 'failed', -1, {
      error: error.message,
      errorStack,
      failedAt: new Date()
    });

    throw error;
  }
}

/**
 * Get job status from MongoDB
 * @param {string} jobId - Job identifier
 * @returns {Promise<Object>} Job document
 */
async function getJobStatus(jobId) {
  const db = await getDb();
  const jobsCollection = db.collection('jobs');
  
  const job = await jobsCollection.findOne({ jobId });
  
  if (!job) {
    throw new Error(`Job ${jobId} not found`);
  }
  
  return job;
}

/**
 * Self-test function - only runs when file is executed directly
 * Set TEST_REPO_URL environment variable to test
 */
async function selfTest() {
  const testRepoUrl = process.env.TEST_REPO_URL;
  
  if (!testRepoUrl) {
    console.log('Self-test skipped: Set TEST_REPO_URL environment variable to run test');
    return;
  }

  console.log(`Starting self-test with repo: ${testRepoUrl}`);
  
  try {
    const result = await ingestRepository(testRepoUrl, { startedBy: 'self-test' });
    console.log('Self-test PASSED:', result);
  } catch (error) {
    console.error('Self-test FAILED:', error);
    process.exit(1);
  }
}

// Run self-test if executed directly
if (require.main === module) {
  selfTest().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

module.exports = {
  ingestRepository,
  getJobStatus,
  // Export helpers for unit testing
  postChunksInBatches,
  validateRepoUrl,
  maskSecrets
};
