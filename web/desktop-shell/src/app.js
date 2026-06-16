(function () {
  var bridge = window.MoneyAppBridge;
  var baseUrlInput = document.getElementById("baseUrl");
  var tradeDateInput = document.getElementById("tradeDate");
  var saveConfigButton = document.getElementById("saveConfig");
  var pingHostButton = document.getElementById("pingHost");
  var hostState = document.getElementById("hostState");
  var requestState = document.getElementById("requestState");
  var requestHistory = document.getElementById("requestHistory");
  var hostLog = document.getElementById("hostLog");
  var metricElapsed = document.getElementById("metricElapsed");
  var metricCache = document.getElementById("metricCache");
  var metricSource = document.getElementById("metricSource");
  var metricDegraded = document.getElementById("metricDegraded");
  var homeView = document.getElementById("homeView");
  var resultView = document.getElementById("resultView");
  var resultTitle = document.getElementById("resultTitle");
  var resultSubtitle = document.getElementById("resultSubtitle");
  var statusStrip = document.getElementById("statusStrip");
  var resultContent = document.getElementById("resultContent");
  var backHomeButton = document.getElementById("backHome");
  var refreshCurrentButton = document.getElementById("refreshCurrent");
  var screenButtons = document.querySelectorAll("[data-screen]");

  var SCREEN_LABELS = {
    "market-signal": "情绪信号",
    "second-board-analysis": "二板解析",
    "board-top10-limit-up": "板块个股排名"
  };

  var state = {
    currentScreen: null,
    latestElapsedMs: null,
    requestItems: [],
    hostItems: []
  };

  function normalizeBaseUrl(baseUrl) {
    if (!baseUrl) {
      return "";
    }
    return /\/$/.test(baseUrl) ? baseUrl : baseUrl + "/";
  }

  function safeOriginBaseUrl() {
    if (window.location && /^https?:/i.test(window.location.protocol)) {
      return normalizeBaseUrl(window.location.origin);
    }
    return "http://47.107.125.248:8080/";
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function stringifyJson(value) {
    if (window.JSON && window.JSON.stringify) {
      return window.JSON.stringify(value);
    }
    return "" + value;
  }

  function parseJson(text) {
    if (window.JSON && window.JSON.parse) {
      return window.JSON.parse(text);
    }
    return eval("(" + text + ")");
  }

  function pad2(value) {
    var text = String(value);
    return text.length < 2 ? "0" + text : text;
  }

  function renderList(container, items) {
    var html = "";
    var i;
    if (!items.length) {
      container.innerHTML = '<div class="empty-state">暂无记录</div>';
      return;
    }
    for (i = 0; i < items.length; i += 1) {
      html += '<div class="history-item"><div>' + escapeHtml(items[i].title) +
        '</div><small>' + escapeHtml(items[i].subtitle) + '</small></div>';
    }
    container.innerHTML = html;
  }

  function pushRequestHistory(title, subtitle) {
    state.requestItems.unshift({ title: title, subtitle: subtitle });
    state.requestItems = state.requestItems.slice(0, 12);
    renderList(requestHistory, state.requestItems);
  }

  function pushHostLog(title, subtitle) {
    state.hostItems.unshift({ title: title, subtitle: subtitle });
    state.hostItems = state.hostItems.slice(0, 20);
    renderList(hostLog, state.hostItems);
  }

  function setHostState(text) {
    hostState.innerHTML = escapeHtml(text);
  }

  function setRequestState(text) {
    requestState.innerHTML = escapeHtml(text);
  }

  function showView(viewName) {
    if (viewName === "home") {
      homeView.className = "panel view active";
      resultView.className = "panel view";
    } else {
      homeView.className = "panel view";
      resultView.className = "panel view active";
    }
  }

  function updateDiagnostics(meta, elapsedMs) {
    metricElapsed.innerHTML = elapsedMs == null ? "--" : (elapsedMs + " ms");
    metricCache.innerHTML = meta ? (meta.cacheHit ? "是" : "否") : "--";
    metricSource.innerHTML = meta && meta.source ? escapeHtml(meta.source) : "--";
    metricDegraded.innerHTML = meta ? (meta.degraded ? "是" : "否") : "--";
  }

  function buildStatusStrip(meta) {
    var chips = [];
    var html = "";
    var i;
    if (!meta) {
      statusStrip.innerHTML = "";
      return;
    }
    chips.push("requestId: " + (meta.requestId || "--"));
    chips.push("clientType: " + (meta.clientType || "--"));
    chips.push("source: " + (meta.source || "--"));
    chips.push("cacheHit: " + (meta.cacheHit ? "true" : "false"));
    chips.push("degraded: " + (meta.degraded ? "true" : "false"));
    if (meta.upstreamSource) {
      chips.push("upstream: " + meta.upstreamSource);
    }
    for (i = 0; i < chips.length; i += 1) {
      html += '<span class="status-chip">' + escapeHtml(chips[i]) + '</span>';
    }
    statusStrip.innerHTML = html;
  }

  function renderNotes(notes) {
    var html = "";
    var i;
    if (!notes || !notes.length) {
      return '<div class="empty-state">暂无备注</div>';
    }
    html += '<ul class="notes-list">';
    for (i = 0; i < notes.length; i += 1) {
      html += '<li>' + escapeHtml(notes[i]) + '</li>';
    }
    html += '</ul>';
    return html;
  }

  function renderMetric(label, value) {
    return '<div class="metric"><b>' + escapeHtml(label) + '</b><span>' + escapeHtml(value) + '</span></div>';
  }

  function renderMarketSignal(data) {
    var indicators = "";
    var i;
    var item;
    for (i = 0; i < (data.indicators || []).length; i += 1) {
      item = data.indicators[i];
      indicators += '<div class="indicator-row"><div>' + escapeHtml(item.name) +
        '</div><div>' + escapeHtml(item.todayValue) +
        '</div><div>' + escapeHtml(item.standard) +
        '</div><div>' + escapeHtml(item.status) + '</div></div>';
    }

    resultContent.innerHTML =
      '<section class="summary-card">' +
      '<h3>' + escapeHtml(data.trade_date || "--") + ' ' + escapeHtml(data.weekday || "") + '</h3>' +
      '<div class="summary-grid">' +
      renderMetric("大盘表现", data.marketOverview || "--") +
      renderMetric("成交额", data.turnoverOverview || "--") +
      renderMetric("情绪判定", data.regimeLabel || "--") +
      renderMetric("仓位建议", data.positionAdvice || "--") +
      '</div></section>' +
      '<section class="indicator-table">' +
      '<div class="indicator-row header"><div>指标</div><div>今日数值</div><div>系统标准</div><div>状态</div></div>' +
      (indicators || '<div class="empty-state">暂无指标</div>') +
      '</section>' +
      '<section class="summary-card"><h3>备注</h3>' + renderNotes(data.notes) + '</section>';
  }

  function renderScreening(data, screen) {
    var summary = data.market_summary || {};
    var items = data.items || [];
    var html = '';
    var i;
    var item;
    var showSecondBoardMetrics = screen === "second-board-analysis";
    var showTotalScoreMetric = !showSecondBoardMetrics;
    html += '<section class="summary-card"><h3>' + escapeHtml(summary.tradeDate || data.trade_date || "--") + '</h3>';
    html += '<div class="summary-grid">' +
      renderMetric("涨停总数", summary.limitUpCount == null ? "--" : String(summary.limitUpCount)) +
      renderMetric("二板数量", summary.secondBoardCount == null ? "--" : String(summary.secondBoardCount)) +
      renderMetric("数据来源", summary.source || "--") +
      '</div>';
    html += '<div class="summary-card" style="margin-top:12px;padding:12px;"><h3>备注</h3>' + renderNotes(summary.notes) + '</div>';
    html += '</section>';

    if (!items.length) {
      html += '<div class="empty-state">当日无符合条件标的</div>';
      resultContent.innerHTML = html;
      return;
    }

    for (i = 0; i < items.length; i += 1) {
      item = items[i];
      html += '<article class="item-card"><h3>' + escapeHtml(item.stockName) + '</h3><div class="item-grid">' +
        (showSecondBoardMetrics ? renderMetric("股价", item.latestPrice || "--") : "") +
        renderMetric("流通市值", item.floatMarketCap || "--") +
        renderMetric("所属板块", item.boardName || "--") +
        (showSecondBoardMetrics ? "" : renderMetric("连板天梯", item.ladderLevel || "--")) +
        renderMetric("板块排名", item.boardRank == null ? "--" : String(item.boardRank)) +
        (showTotalScoreMetric ? renderMetric("总分", item.totalScore == null ? "--" : String(item.totalScore)) : "") +
        (showSecondBoardMetrics ? renderMetric("板块涨停数", item.boardLimitUpCount == null ? "--" : String(item.boardLimitUpCount)) : "") +
        renderMetric("封单时间", item.sealTime || "--") +
        renderMetric("封单手数", item.sealOrderLots || "--") +
        renderMetric("开板次数", item.openBoardCount == null ? "--" : String(item.openBoardCount)) +
        renderMetric("换手率", item.turnoverRate || "--") +
        (showSecondBoardMetrics ? renderMetric("首板量能", item.firstBoardEnergy || "--") : renderMetric("板块涨停数", item.boardLimitUpCount == null ? "--" : String(item.boardLimitUpCount))) +
        '</div><p>' + escapeHtml(item.recommendReason || "--") + '</p></article>';
    }

    resultContent.innerHTML = html;
  }

  function renderEnvelope(screen, envelope) {
    updateDiagnostics(envelope && envelope.meta ? envelope.meta : null, state.latestElapsedMs);
    buildStatusStrip(envelope && envelope.meta ? envelope.meta : null);

    if (!envelope || !envelope.success) {
      resultContent.innerHTML =
        '<section class="error-card"><h3>请求失败</h3><p>' +
        escapeHtml((envelope && envelope.error && envelope.error.message) || "未知错误") +
        '</p><pre>' + escapeHtml(stringifyJson(envelope && envelope.error ? envelope.error : envelope)) +
        '</pre></section>';
      return;
    }

    if (screen === "market-signal") {
      renderMarketSignal(envelope.data);
    } else {
      renderScreening(envelope.data, screen);
    }
  }

  function buildRequestBody(forceRefresh) {
    var tradeDate = tradeDateInput.value.replace(/^\s+|\s+$/g, "");
    return {
      trade_date: tradeDate || null,
      use_demo_on_failure: true,
      force_refresh: !!forceRefresh
    };
  }

  function requestScreen(screen, forceRefresh) {
    var baseUrl = normalizeBaseUrl(baseUrlInput.value.replace(/^\s+|\s+$/g, "")) || safeOriginBaseUrl();
    var path = screen;
    var label = SCREEN_LABELS[screen] || screen;
    var requestInfo = {
      type: "web.request.log",
      payload: {
        path: "/api/v1/screen/" + path,
        method: "POST",
        startedAt: new Date().toISOString(),
        baseUrl: baseUrl
      }
    };
    var xhr = new XMLHttpRequest();
    var started = new Date().getTime();

    state.currentScreen = screen;
    resultTitle.innerHTML = escapeHtml(label);
    resultSubtitle.innerHTML = forceRefresh ? "强制刷新中..." : "加载中...";
    setRequestState("请求中: " + label);
    showView("result");
    pushRequestHistory(label + " queued", requestInfo.payload.method + " " + requestInfo.payload.path);
    bridge.postHostMessage(requestInfo);

    xhr.open("POST", baseUrl + "api/v1/screen/" + path, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-Client-Type", "web-desktop");
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) {
        return;
      }

      state.latestElapsedMs = new Date().getTime() - started;
      if (xhr.status >= 200 && xhr.status < 300) {
        var body = parseJson(xhr.responseText);
        resultSubtitle.innerHTML = label + " 返回完成";
        setRequestState("最近请求: " + label);
        pushRequestHistory(label + " done", "status=" + xhr.status + " elapsed=" + state.latestElapsedMs + "ms");
        renderEnvelope(screen, body);
      } else {
        resultSubtitle.innerHTML = label + " 请求失败";
        setRequestState("失败: " + label);
        pushRequestHistory(label + " error", "status=" + xhr.status);
        renderEnvelope(screen, {
          success: false,
          error: {
            message: "HTTP " + xhr.status,
            detail: xhr.responseText
          }
        });
      }
    };
    xhr.send(stringifyJson(buildRequestBody(forceRefresh)));
  }

  function readStoredConfig() {
    var today;
    try {
      var storedBaseUrl = window.localStorage.getItem("moneyapp.desktop.baseUrl");
      var storedTradeDate = window.localStorage.getItem("moneyapp.desktop.tradeDate");
      if (storedBaseUrl) {
        baseUrlInput.value = storedBaseUrl;
      } else {
        baseUrlInput.value = safeOriginBaseUrl();
      }
      if (storedTradeDate) {
        tradeDateInput.value = storedTradeDate;
      } else {
        today = new Date();
        tradeDateInput.value = today.getFullYear() + "-" +
          pad2(today.getMonth() + 1) + "-" +
          pad2(today.getDate());
      }
    } catch (error) {
      baseUrlInput.value = safeOriginBaseUrl();
      today = new Date();
      tradeDateInput.value = today.getFullYear() + "-" +
        pad2(today.getMonth() + 1) + "-" +
        pad2(today.getDate());
    }
  }

  function saveLocalConfig() {
    try {
      window.localStorage.setItem("moneyapp.desktop.baseUrl", normalizeBaseUrl(baseUrlInput.value.replace(/^\s+|\s+$/g, "")));
      window.localStorage.setItem("moneyapp.desktop.tradeDate", tradeDateInput.value.replace(/^\s+|\s+$/g, ""));
    } catch (error) {
      pushHostLog("localStorage", "save failed");
    }
  }

  function handleHostMessage(message) {
    var payload;
    try {
      payload = typeof message === "string" ? parseJson(message) : message;
    } catch (error) {
      payload = { type: "host.raw", payload: { raw: String(message) } };
    }

    if (payload.type === "host.config.sync" && payload.payload && payload.payload.baseUrl) {
      baseUrlInput.value = payload.payload.baseUrl;
      setHostState("已连接 · " + (payload.payload.clientType || "client"));
      pushHostLog("host.config.sync", payload.payload.baseUrl);
      saveLocalConfig();
      return;
    }

    if (payload.type === "host.request.received") {
      pushHostLog("host.request.received", payload.payload.method + " " + payload.payload.path);
      return;
    }

    if (payload.type === "host.status") {
      setHostState("已连接");
      pushHostLog("host." + payload.payload.level, payload.payload.message);
      return;
    }

    pushHostLog(payload.type || "host.message", stringifyJson(payload.payload || payload));
  }

  function initialize() {
    var i;
    renderList(requestHistory, []);
    renderList(hostLog, []);
    showView("home");
    updateDiagnostics(null, null);
    readStoredConfig();

    for (i = 0; i < screenButtons.length; i += 1) {
      screenButtons[i].onclick = function () {
        requestScreen(this.getAttribute("data-screen"), false);
      };
    }

    saveConfigButton.onclick = function () {
      var normalizedBaseUrl = normalizeBaseUrl(baseUrlInput.value.replace(/^\s+|\s+$/g, "")) || safeOriginBaseUrl();
      baseUrlInput.value = normalizedBaseUrl;
      saveLocalConfig();
      bridge.postHostMessage({
        type: "host.config.save",
        payload: {
          baseUrl: normalizedBaseUrl,
          clientType: "windows-mfc"
        }
      });
      pushHostLog("host.config.save", normalizedBaseUrl);
    };

    pingHostButton.onclick = function () {
      bridge.postHostMessage({ type: "host.ping", payload: {} });
      pushHostLog("host.ping", "sent");
    };

    backHomeButton.onclick = function () {
      showView("home");
      setRequestState("已返回");
    };

    refreshCurrentButton.onclick = function () {
      if (state.currentScreen) {
        requestScreen(state.currentScreen, true);
      }
    };

    bridge.listenHostMessages(handleHostMessage);
    if (bridge.hasWebViewBridge()) {
      setHostState("正在连接…");
      bridge.postHostMessage({ type: "host.ping", payload: {} });
    } else {
      setHostState("独立浏览");
      pushHostLog("host.bridge", "not available");
    }
  }

  initialize();
})();
