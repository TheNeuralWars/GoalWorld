(function () {
  /** Canonical transactional frontend (Vercel / goalworld_webapp). */
  var PLAY = window.goalworld_PLAY_URL || 'https://play.goalworld.fun';
  window.goalworld_PLAY_URL = PLAY;
  /** Marketing-site alias; GitHub Pages serves docs/go/index.html → play URL. */
  window.goalworld_PLAY_PATH = window.goalworld_PLAY_PATH || '/go/';

  /**
   * Resolve a /go/... (or bare path) to the canonical play URL.
   *   /go/         -> https://play.goalworld.fun/
   *   /go/estadio  -> https://play.goalworld.fun/estadio
   *   estadio      -> https://play.goalworld.fun/estadio
   */
  window.goalworldPlayUrl = function (path) {
    if (!path || path === '/go' || path === '/go/') return PLAY + '/';
    if (path.indexOf('/go/') === 0) path = path.slice(3);      // strip "/go"
    else if (path.indexOf('/go') === 0) path = path.slice(3);
    if (path.charAt(0) !== '/' && path.charAt(0) !== '#') path = '/' + path;
    return PLAY + path;
  };

  /** Global helper for inline onclick handlers. */
  window.goToPlay = function (path) {
    window.location.href = window.goalworldPlayUrl(path);
  };

  /** Rewrite all anchors pointing at /go/... so they resolve on any host. */
  function rewriteLinks() {
    document.querySelectorAll('a[href^="/go"]').forEach(function (a) {
      a.href = window.goalworldPlayUrl(a.getAttribute('href'));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', rewriteLinks);
  } else {
    rewriteLinks();
  }
})();
