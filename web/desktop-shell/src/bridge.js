(function (global) {
  function hasWebViewBridge() {
    return !!(global.chrome && global.chrome.webview && global.chrome.webview.postMessage);
  }

  function postHostMessage(message) {
    var payload = typeof message === "string" ? message : JSON.stringify(message);
    if (hasWebViewBridge()) {
      global.chrome.webview.postMessage(payload);
      return true;
    }
    return false;
  }

  function listenHostMessages(callback) {
    if (hasWebViewBridge() && global.chrome.webview.addEventListener) {
      global.chrome.webview.addEventListener("message", function (event) {
        callback(event.data);
      });
    }
  }

  global.MoneyAppBridge = {
    hasWebViewBridge: hasWebViewBridge,
    postHostMessage: postHostMessage,
    listenHostMessages: listenHostMessages,
  };
})(window);
