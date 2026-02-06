const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const MAX_BUNDLE_SIZE = 500 * 1024; // 500KB gzipped

function getGzipSize(filePath) {
  const content = fs.readFileSync(filePath);
  return zlib.gzipSync(content).length;
}

function collectJsFiles(dir) {
  const files = [];
  if (!fs.existsSync(dir)) return files;

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectJsFiles(fullPath));
    } else if (entry.name.endsWith(".js")) {
      files.push(fullPath);
    }
  }
  return files;
}

function checkBundleSize() {
  const chunksDir = path.join(__dirname, "../.next/static/chunks");
  const appDir = path.join(__dirname, "../.next/static/chunks/app");

  if (!fs.existsSync(chunksDir)) {
    console.error("Build directory not found. Run 'npm run build' first.");
    process.exit(1);
  }

  let totalGzipSize = 0;
  const seen = new Set();

  for (const dir of [chunksDir, appDir]) {
    const files = collectJsFiles(dir);
    for (const filePath of files) {
      if (seen.has(filePath)) continue;
      seen.add(filePath);

      const rawSize = fs.statSync(filePath).size;
      const gzipSize = getGzipSize(filePath);
      const relativePath = path.relative(path.join(__dirname, ".."), filePath);

      totalGzipSize += gzipSize;
      console.log(
        `${relativePath}: ${(rawSize / 1024).toFixed(2)} KB (gzip: ${(gzipSize / 1024).toFixed(2)} KB)`
      );
    }
  }

  console.log(`\nTotal gzipped bundle size: ${(totalGzipSize / 1024).toFixed(2)} KB`);

  if (totalGzipSize > MAX_BUNDLE_SIZE) {
    console.error(
      `\nBundle size exceeds ${MAX_BUNDLE_SIZE / 1024} KB gzipped limit!`
    );
    process.exit(1);
  } else {
    console.log(
      `\nBundle size is within ${MAX_BUNDLE_SIZE / 1024} KB gzipped limit.`
    );
  }
}

checkBundleSize();
