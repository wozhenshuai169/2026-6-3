const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', 'Scripts', 'python.exe');
const outputDir = path.join(root, 'qa', 'mobile-portrait');
const baseUrl = 'http://127.0.0.1:8765';
const browserExecutable = process.env.PLAYWRIGHT_BROWSER_PATH
  || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const pages = [
  ['landing', '/pages/landing/index.html'],
  ['visitor', '/pages/user-portal/index.html'],
  ['recommend', '/pages/recommend/index.html'],
  ['vision', '/pages/vision/index.html'],
  ['assistant', '/pages/ai-assistant/index.html'],
  ['guide', '/pages/guide-panel/index.html'],
  ['dashboard', '/pages/dashboard/index.html'],
  ['knowledge', '/pages/knowledge-base/index.html'],
  ['avatar', '/pages/avatar-studio/index.html'],
];

async function waitForServer() {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/health/ready`);
      if (response.ok) return;
    } catch (_) {
      // The server is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error('Timed out waiting for the local acceptance server');
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const server = spawn(
    python,
    ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8765'],
    { cwd: root, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] },
  );
  let serverError = '';
  server.stderr.on('data', (chunk) => { serverError += chunk.toString(); });

  let browser;
  try {
    await waitForServer();
    browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 1,
      isMobile: true,
      hasTouch: true,
    });
    const results = [];
    for (const [name, url] of pages) {
      const page = await context.newPage();
      await page.route('**/*.js', (route) => route.abort());
      await page.goto(`${baseUrl}${url}`, { waitUntil: 'networkidle' });
      const metrics = await page.evaluate(() => ({
        viewportWidth: window.innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        bodyWidth: document.body.scrollWidth,
      }));
      const overflow = Math.max(metrics.documentWidth, metrics.bodyWidth) - metrics.viewportWidth;
      await page.screenshot({
        path: path.join(outputDir, `${name}-390x844.png`),
        fullPage: true,
      });
      results.push({ name, overflow, ...metrics });
      await page.close();
    }
    await context.close();
    const failures = results.filter((item) => item.overflow > 1);
    console.log(JSON.stringify(results, null, 2));
    if (failures.length) {
      throw new Error(`Horizontal overflow detected: ${failures.map((item) => `${item.name}=${item.overflow}px`).join(', ')}`);
    }
  } finally {
    if (browser) await browser.close();
    server.kill();
  }
  if (serverError && /error|traceback/i.test(serverError)) {
    throw new Error(serverError);
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
