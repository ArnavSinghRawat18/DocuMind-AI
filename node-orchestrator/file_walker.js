/**
 * node-orchestrator/file_walker.js
 * Recursively scans repository directories for code files.
 * Filters by extension and ignores common non-code directories.
 */

const fs = require('fs');
const path = require('path');

// Allowed file extensions (matches Python backend config)
const ALLOWED_EXTENSIONS = new Set([
  '.py', '.js', '.ts', '.md', '.jsx', '.tsx', '.java', '.go', '.rs'
]);

// Directories to ignore during traversal
const IGNORED_DIRECTORIES = new Set([
  '.git', 'node_modules', 'venv', '__pycache__',
  'dist', 'build', '.venv', 'env', '.env',
  '.idea', '.vscode', 'coverage', '.pytest_cache',
  'target', 'vendor', '.tox', '.mypy_cache'
]);

// Maximum file size in bytes (10MB)
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

/**
 * Recursively scans a directory for code files.
 * @param {string} rootPath - Absolute path to the repository root
 * @returns {Promise<string[]>} - Array of absolute file paths
 */
async function scanFiles(rootPath) {
  const files = [];

  if (!fs.existsSync(rootPath)) {
    console.error(`[file_walker] Directory does not exist: ${rootPath}`);
    return files;
  }

  const stats = fs.statSync(rootPath);
  if (!stats.isDirectory()) {
    console.error(`[file_walker] Path is not a directory: ${rootPath}`);
    return files;
  }

  console.log(`[file_walker] Scanning directory: ${rootPath}`);

  /**
   * Internal recursive walker
   * @param {string} currentDir - Current directory being scanned
   */
  function walkDir(currentDir) {
    let entries;
    try {
      entries = fs.readdirSync(currentDir, { withFileTypes: true });
    } catch (err) {
      console.warn(`[file_walker] Cannot read directory: ${currentDir} - ${err.message}`);
      return;
    }

    for (const entry of entries) {
      const fullPath = path.join(currentDir, entry.name);

      if (entry.isDirectory()) {
        // Skip ignored directories and hidden folders
        if (IGNORED_DIRECTORIES.has(entry.name) || entry.name.startsWith('.')) {
          continue;
        }
        walkDir(fullPath);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();

        // Check extension
        if (!ALLOWED_EXTENSIONS.has(ext)) {
          continue;
        }

        // Check file size
        try {
          const fileStats = fs.statSync(fullPath);
          if (fileStats.size > MAX_FILE_SIZE_BYTES) {
            console.warn(`[file_walker] Skipping large file (${(fileStats.size / 1024 / 1024).toFixed(2)}MB): ${fullPath}`);
            continue;
          }
          files.push(fullPath);
        } catch (err) {
          console.warn(`[file_walker] Cannot stat file: ${fullPath} - ${err.message}`);
        }
      }
    }
  }

  walkDir(rootPath);

  console.log(`[file_walker] Discovered ${files.length} files`);
  return files;
}

module.exports = {
  scanFiles
};
