/**
 * node-orchestrator/db/mongo.js
 * MongoDB connection module for DocuMind AI
 * Provides a singleton connection with idempotent connect() and getDb() accessors
 */

const { MongoClient } = require('mongodb');

// Private module-level state
let client = null;
let db = null;

/**
 * Validates environment variables and returns connection config
 * @returns {{ uri: string, dbName: string }}
 * @throws {Error} If MONGO_URI is missing or invalid
 */
function getConfig() {
  const uri = process.env.MONGO_URI;
  const dbName = process.env.DB_NAME || 'documind_dev';

  if (!uri) {
    throw new Error('[mongo] Missing MONGO_URI environment variable. Please set it in your .env file.');
  }

  if (!uri.startsWith('mongodb://') && !uri.startsWith('mongodb+srv://')) {
    throw new Error('[mongo] Invalid MONGO_URI. Must start with mongodb:// or mongodb+srv://');
  }

  return { uri, dbName };
}

/**
 * Connects to MongoDB using a singleton client.
 * Idempotent: calling multiple times will not create multiple connections.
 * @returns {Promise<void>}
 * @throws {Error} If connection fails or env vars are invalid
 */
async function connect() {
  // Already connected — skip
  if (client && db) {
    console.log('[mongo] Already connected, skipping...');
    return;
  }

  const { uri, dbName } = getConfig();

  try {
    console.log('[mongo] Connecting to MongoDB...');

    // Create client (no deprecated options needed for mongodb driver 6+)
    client = new MongoClient(uri);

    // Establish connection
    await client.connect();

    // Get database reference
    db = client.db(dbName);

    console.log(`[mongo] Connected successfully to database: ${dbName}`);

  } catch (error) {
    console.error('[mongo] Connection failed:', error.message);
    
    // Reset state on failure
    client = null;
    db = null;

    throw error;
  }
}

/**
 * Returns the active database instance.
 * Must call connect() before using this function.
 * @returns {import('mongodb').Db} The MongoDB database instance
 * @throws {Error} If connect() was not called first
 */
function getDb() {
  if (!db) {
    throw new Error('[mongo] Database not initialized. Call connect() first.');
  }

  return db;
}

/**
 * Returns the active MongoClient instance (for advanced use cases).
 * @returns {MongoClient|null} The MongoDB client or null if not connected
 */
function getClient() {
  return client;
}

/**
 * Closes the MongoDB connection gracefully.
 * @returns {Promise<void>}
 */
async function disconnect() {
  if (client) {
    console.log('[mongo] Disconnecting...');
    await client.close();
    client = null;
    db = null;
    console.log('[mongo] Disconnected successfully');
  }
}

module.exports = {
  connect,
  getDb,
  getClient,
  disconnect
};
