const { chromium } = require('playwright');

const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:8000';
const browserExecutable = process.env.PLAYWRIGHT_BROWSER_PATH
  || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const pages = [
  'landing', 'user-portal', 'recommend', 'vision', 'ai-assistant',
  'guide-panel', 'dashboard', 'knowledge-base', 'avatar-studio',
];

async function verifyContext(browser, viewport, reducedMotion) {
  const context = await browser.newContext({ viewport, reducedMotion });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));

  for (const name of pages) {
    await page.goto(`${baseUrl}/pages/${name}/index.html`, { waitUntil: 'networkidle' });
    const state = await page.evaluate(() => ({
      direction: document.documentElement.dataset.navigationDirection,
      hasNavigator: typeof Aurelian.navigateWithMotion === 'function',
      hasBackNavigator: typeof Aurelian.navigateBack === 'function',
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      bodyAnimation: getComputedStyle(document.body).animationName,
    }));
    if (!state.hasNavigator || !state.hasBackNavigator) throw new Error(`${name}: navigation helpers missing`);
    if (state.overflow > 1) throw new Error(`${name}: horizontal overflow ${state.overflow}px`);
    if (state.bodyAnimation !== 'none') throw new Error(`${name}: legacy body animation still active`);
  }

  await page.goto(`${baseUrl}/pages/vision/index.html`, { waitUntil: 'networkidle' });
  await page.evaluate(() => Aurelian.navigateWithMotion('../recommend/index.html'));
  await page.waitForURL('**/pages/recommend/index.html');
  if ((await page.locator('html').getAttribute('data-navigation-direction')) !== 'forward') {
    throw new Error('Forward navigation direction was not preserved');
  }

  await page.evaluate(() => Aurelian.navigateBack('../landing/index.html'));
  await page.waitForURL('**/pages/vision/index.html');
  if ((await page.locator('html').getAttribute('data-navigation-direction')) !== 'back') {
    throw new Error('Back navigation direction was not preserved');
  }

  if (errors.length) throw new Error(`Browser errors: ${errors.join(' | ')}`);
  await context.close();
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
  try {
    await verifyContext(browser, { width: 390, height: 844 }, 'no-preference');
    await verifyContext(browser, { width: 1440, height: 900 }, 'no-preference');
    await verifyContext(browser, { width: 390, height: 844 }, 'reduce');
    console.log('Page transition verification passed: 9 pages, mobile/desktop/reduced-motion.');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
