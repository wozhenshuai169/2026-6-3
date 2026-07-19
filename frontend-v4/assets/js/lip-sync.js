(function (global) {
  'use strict';

  var root = global.Aurelian = global.Aurelian || {};

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function attach(audio, mouth) {
    var enabled = true;
    var frameImage = null;
    var showingOpenFrame = false;
    var lastFrameSwitchAt = 0;
    var context = null;
    var analyser = null;
    var source = null;
    var samples = null;
    var frameId = 0;
    var smoothed = 0;
    var silentFrames = 0;

    function resolveFrameImage() {
      if (mouth && mouth.matches && mouth.matches('img')) return mouth;
      if (!mouth || !mouth.parentElement) return null;
      return mouth.parentElement.querySelector('img[data-speaking-src], img[data-closed-src]');
    }

    function setLevel(level) {
      if (!mouth) return;
      var activeLevel = enabled ? level : 0;
      mouth.setAttribute('data-mouth-level', String(activeLevel));
      frameImage = resolveFrameImage();
      if (!frameImage) return;
      var closedValue = frameImage.getAttribute('data-closed-src') || frameImage.src || '';
      var configuredOpenSrc = frameImage.getAttribute('data-speaking-src') || '';
      var closedSrc = closedValue ? new URL(closedValue, document.baseURI).href : '';
      var speakingSrc = configuredOpenSrc ? new URL(configuredOpenSrc, document.baseURI).href : '';
      var hasSpeakingFrame = Boolean(speakingSrc);
      if (mouth !== frameImage) mouth.hidden = hasSpeakingFrame;
      if (!hasSpeakingFrame) {
        showingOpenFrame = false;
        return;
      }

      var currentSrc = frameImage.currentSrc || frameImage.src || '';
      if (currentSrc === closedSrc && showingOpenFrame) {
        showingOpenFrame = false;
        lastFrameSwitchAt = 0;
      } else if (currentSrc === speakingSrc && !showingOpenFrame) {
        showingOpenFrame = true;
        lastFrameSwitchAt = 0;
      }

      var now = global.performance && global.performance.now ? global.performance.now() : Date.now();
      var shouldOpen = activeLevel > 0;
      var minimumHold = showingOpenFrame ? 78 : 42;
      if (shouldOpen === showingOpenFrame || now - lastFrameSwitchAt < minimumHold) return;
      frameImage.src = shouldOpen ? speakingSrc : closedSrc;
      showingOpenFrame = shouldOpen;
      lastFrameSwitchAt = now;
    }

    function ensureGraph() {
      if (analyser || !audio) return analyser;
      var AudioContext = global.AudioContext || global.webkitAudioContext;
      if (!AudioContext) return null;
      try {
        context = new AudioContext();
        analyser = context.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = .68;
        source = context.createMediaElementSource(audio);
        source.connect(analyser);
        analyser.connect(context.destination);
        samples = new Uint8Array(analyser.fftSize);
      } catch (error) {
        analyser = null;
      }
      return analyser;
    }

    function readEnergy() {
      if (!analyser || !samples) return 0;
      analyser.getByteTimeDomainData(samples);
      var sum = 0;
      for (var index = 0; index < samples.length; index += 1) {
        var centered = (samples[index] - 128) / 128;
        sum += centered * centered;
      }
      return Math.sqrt(sum / samples.length);
    }

    function animate() {
      if (!audio || audio.paused || audio.ended || !enabled) {
        setLevel(0);
        frameId = 0;
        return;
      }

      var energy = readEnergy();
      silentFrames = energy < .008 ? silentFrames + 1 : 0;

      // Cross-origin audio without analyser data falls back to a restrained cadence.
      if (!analyser || silentFrames > 24) {
        var phase = audio.currentTime * 12.5;
        var phraseGate = Math.sin(audio.currentTime * 2.05 + .4) > -.72 ? 1 : 0;
        energy = phraseGate * (
          .006 + Math.max(0, Math.sin(phase)) * .09 +
          Math.max(0, Math.sin(phase * .53 + .7)) * .028
        );
      }

      var normalized = clamp((energy - .012) / .13, 0, 1);
      smoothed = smoothed * .62 + normalized * .38;
      var level = smoothed < .1 ? 0 : smoothed < .3 ? 1 : smoothed < .62 ? 2 : 3;
      setLevel(level);
      frameId = global.requestAnimationFrame(animate);
    }

    function start() {
      if (!enabled || !audio) return;
      ensureGraph();
      if (context && context.state === 'suspended') context.resume().catch(function () {});
      if (!frameId) frameId = global.requestAnimationFrame(animate);
    }

    function stop() {
      if (frameId) global.cancelAnimationFrame(frameId);
      frameId = 0;
      smoothed = 0;
      silentFrames = 0;
      lastFrameSwitchAt = 0;
      setLevel(0);
    }

    if (audio) {
      audio.addEventListener('play', start);
      audio.addEventListener('pause', stop);
      audio.addEventListener('ended', stop);
      audio.addEventListener('emptied', stop);
    }
    frameImage = resolveFrameImage();
    if (frameImage && frameImage.getAttribute('data-speaking-src')) {
      var preload = new Image();
      preload.src = new URL(frameImage.getAttribute('data-speaking-src'), document.baseURI).href;
    }
    setLevel(0);

    return {
      setEnabled: function (nextEnabled) {
        enabled = nextEnabled !== false;
        if (enabled && audio && !audio.paused) start();
        else stop();
      },
      stop: stop
    };
  }

  root.lipSync = { attach: attach };
})(window);
