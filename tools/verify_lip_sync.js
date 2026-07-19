const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const imageRoot = path.join(root, 'frontend-v4', 'assets', 'images');
const expectedFrames = {
  guide_female: ['digital-guide-foreground.png', 'digital-guide-foreground-open.png'],
  xiaomei: ['digital-avatar-b.png', 'digital-avatar-b-open.png'],
  guide_male: ['digital-avatar-a.png', 'digital-avatar-a-open.png'],
  xiaowei: ['digital-avatar-professional-male.png', 'digital-avatar-professional-male-open.png'],
};

for (const frames of Object.values(expectedFrames)) {
  for (const filename of frames) {
    if (!fs.existsSync(path.join(imageRoot, filename))) {
      throw new Error(`Missing lip-sync frame: ${filename}`);
    }
  }
}

const visitorScript = fs.readFileSync(
  path.join(root, 'frontend-v4', 'assets', 'js', 'pages', 'visitor-unified.js'),
  'utf8',
);
const leaderScript = fs.readFileSync(
  path.join(root, 'frontend-v4', 'assets', 'js', 'pages', 'guide-panel.js'),
  'utf8',
);
if (!visitorScript.includes('A.lipSync.attach(els.tts, els.guideImage)')) {
  throw new Error('Visitor page is not connected to lip sync');
}
if (!leaderScript.includes('A.lipSync.attach(els.guideNarrationPlayer, els.guideAvatarMouth)')) {
  throw new Error('Leader page is not connected to lip sync');
}

const browserExecutable = process.env.PLAYWRIGHT_BROWSER_PATH
  || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: browserExecutable });
  try {
    const page = await browser.newPage();
    await page.setContent(`
      <base href="http://127.0.0.1:8000/">
      <div id="leader-frame"><img id="leader-image"><span id="leader-mouth"></span></div>
      <audio id="leader-audio"></audio>
      <div id="visitor-frame"><img id="visitor-image"></div>
      <audio id="visitor-audio"></audio>
    `);
    await page.evaluate(() => {
      window.AudioContext = undefined;
      window.webkitAudioContext = undefined;
    });
    await page.addScriptTag({ path: path.join(root, 'frontend-v4', 'assets', 'js', 'avatar-voice-map.js') });
    await page.addScriptTag({ path: path.join(root, 'frontend-v4', 'assets', 'js', 'lip-sync.js') });

    const result = await page.evaluate(async (frames) => {
      let audioTime = 0;
      let paused = false;
      const leaderAudio = document.getElementById('leader-audio');
      const visitorAudio = document.getElementById('visitor-audio');
      [leaderAudio, visitorAudio].forEach((audio) => {
        Object.defineProperty(audio, 'paused', { configurable: true, get: () => paused });
        Object.defineProperty(audio, 'ended', { configurable: true, get: () => false });
        Object.defineProperty(audio, 'currentTime', { configurable: true, get: () => audioTime });
      });

      const leaderImage = document.getElementById('leader-image');
      const leaderFrame = document.getElementById('leader-frame');
      const leaderMouth = document.getElementById('leader-mouth');
      const visitorImage = document.getElementById('visitor-image');
      const visitorFrame = document.getElementById('visitor-frame');
      Aurelian.avatarVoices.apply('guide_female', leaderImage, leaderFrame);
      Aurelian.avatarVoices.apply('guide_female', visitorImage, visitorFrame);
      Aurelian.lipSync.attach(leaderAudio, leaderMouth);
      Aurelian.lipSync.attach(visitorAudio, visitorImage);
      leaderAudio.dispatchEvent(new Event('play'));
      visitorAudio.dispatchEvent(new Event('play'));

      const observations = {};
      for (const [voice, expected] of Object.entries(frames)) {
        audioTime = 0;
        Aurelian.avatarVoices.apply(voice, leaderImage, leaderFrame);
        Aurelian.avatarVoices.apply(voice, visitorImage, visitorFrame);
        const seen = {
          leaderClosed: false,
          leaderOpen: false,
          visitorClosed: false,
          visitorOpen: false,
        };
        for (let index = 0; index < 90; index += 1) {
          audioTime += 0.04;
          await new Promise((resolve) => setTimeout(resolve, 20));
          const leaderSrc = leaderImage.src;
          const visitorSrc = visitorImage.src;
          seen.leaderClosed ||= leaderSrc.endsWith(expected[0]);
          seen.leaderOpen ||= leaderSrc.endsWith(expected[1]);
          seen.visitorClosed ||= visitorSrc.endsWith(expected[0]);
          seen.visitorOpen ||= visitorSrc.endsWith(expected[1]);
        }
        observations[voice] = seen;
      }

      paused = true;
      leaderAudio.dispatchEvent(new Event('pause'));
      visitorAudio.dispatchEvent(new Event('pause'));
      return observations;
    }, expectedFrames);

    for (const [voice, states] of Object.entries(result)) {
      for (const [state, seen] of Object.entries(states)) {
        if (!seen) throw new Error(`${voice}: ${state} frame was never shown`);
      }
    }
    console.log('Lip sync verified: 4 voices switch naturally on leader and visitor render paths.');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
