(function () {
  'use strict';

  window.CompetitionReset = {
    clearLocal: function () {
      try {
        localStorage.removeItem('competition-demo-step');
        sessionStorage.removeItem('competition-demo-runtime');
      } catch (_) {}
    },
    announce: function () {
      try {
        var channel = new BroadcastChannel('competition-demo-control');
        channel.postMessage({ type: 'reset', source: 'competition-reset' });
        channel.close();
      } catch (_) {}
    }
  };
})();
