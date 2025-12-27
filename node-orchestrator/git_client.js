/**
 * node-orchestrator/git_client.js
 * Git operations for DocuMind AI
 * Handles repository cloning with proper cleanup
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Base directory for cloned repos
const REPOS_DIR = process.env.REPOS_DIR || path.join(os.tmpdir(), 'documind-repos');

/**
 * Ensures the repos directory exists
 */
function ensureReposDir() {
  if (!fs.existsSync(REPOS_DIR)) {
    fs.mkdirSync(REPOS_DIR, { recursive: true });
  }
}

/**
 * Clones a Git repository to a local directory
 * @param {string} repoUrl - The repository URL to clone
 * @param {string} jobId - Job identifier for the directory name
 * @returns {Promise<string>} - Path to the cloned repository
 */
async function cloneRepository(repoUrl, jobId) {
  ensureReposDir();
  
  const repoPath = path.join(REPOS_DIR, jobId);
  
  // Clean up if directory already exists
  if (fs.existsSync(repoPath)) {
    fs.rmSync(repoPath, { recursive: true, force: true });
  }
  
  console.log(`[git_client] Cloning ${repoUrl} to ${repoPath}`);
  
  try {
    // Clone with depth=1 for faster cloning (shallow clone)
    execSync(`git clone --depth 1 "${repoUrl}" "${repoPath}"`, {
      stdio: 'pipe',
      timeout: 300000 // 5 minutes timeout
    });
    
    console.log(`[git_client] Successfully cloned to ${repoPath}`);
    return repoPath;
  } catch (error) {
    console.error(`[git_client] Clone failed:`, error.message);
    
    // Clean up on failure
    if (fs.existsSync(repoPath)) {
      fs.rmSync(repoPath, { recursive: true, force: true });
    }
    
    throw new Error(`Failed to clone repository: ${error.message}`);
  }
}

/**
 * Removes a cloned repository
 * @param {string} repoPath - Path to the repository to remove
 */
function cleanupRepository(repoPath) {
  if (fs.existsSync(repoPath)) {
    fs.rmSync(repoPath, { recursive: true, force: true });
    console.log(`[git_client] Cleaned up ${repoPath}`);
  }
}

module.exports = {
  cloneRepository,
  cleanupRepository,
  REPOS_DIR
};
