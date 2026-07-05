/* ============================================================
   SEO Content Generator — Landing Page 前端逻辑
   文件职责：
     1. Demo 表单提交（POST /api/demo）
     2. PayPal 按钮渲染（3 个套餐：single / starter / pro）
     3. thank-you.html 文章生成（POST /api/paypal/generate-article）
   安全：
     - 用户输入统一用 encodeURIComponent 编码进 URL，用 textContent 写入 DOM
     - 服务端返回的 Markdown 先 escape HTML 再渲染，防 XSS
   ============================================================ */
(function () {
  "use strict";

  /* ---------- 工具函数 ---------- */

  /** XSS 安全：转义 HTML 特殊字符 */
  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /** 从 URL 查询参数中安全取值 */
  function getQueryParam(name) {
    var params = new URLSearchParams(window.location.search);
    return params ? params.get(name) : null;
  }

  /** 统一的 fetch JSON 封装（含错误信息提取） */
  function postJSON(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    }).then(function (res) {
      // 即使非 2xx 也尝试解析 JSON 错误信息
      return res.json().then(function (data) {
        if (!res.ok) {
          var msg = (data && (data.error || data.message)) || ("HTTP " + res.status);
          var err = new Error(msg);
          err.payload = data;
          throw err;
        }
        return data;
      });
    });
  }

  /** 把 0-100 分映射成评分等级 class */
  function scoreClass(score) {
    var n = Number(score);
    if (isNaN(n)) return "mid";
    if (n >= 70) return "high";
    if (n >= 40) return "mid";
    return "low";
  }

  /** 取评分数字（兼容 seo_score 为对象或数字的返回结构） */
  function extractScore(seoScore) {
    if (seoScore == null) return null;
    if (typeof seoScore === "number") return seoScore;
    if (typeof seoScore === "object") {
      if (typeof seoScore.score === "number") return seoScore.score;
      if (typeof seoScore.total === "number") return seoScore.total;
    }
    return null;
  }

  /** 取建议数组 */
  function extractSuggestions(seoScore) {
    if (seoScore && typeof seoScore === "object" && Array.isArray(seoScore.suggestions)) {
      return seoScore.suggestions;
    }
    return [];
  }

  /**
   * 安全地把 Markdown 渲染为 HTML 片段。
   * 先 escape 全部 HTML，再在已转义文本上应用 Markdown 子集规则，
   * 因此不会注入原始 HTML / 脚本。
   * 支持：H1-H3、无序列表、有序列表、段落、加粗、行内代码、链接。
   */
  function renderMarkdown(md) {
    if (!md) return "";
    var escaped = escapeHtml(md);
    var lines = escaped.split(/\r?\n/);
    var html = [];
    var inUl = false, inOl = false;
    var paragraphBuffer = [];

    function flushParagraph() {
      if (paragraphBuffer.length) {
        html.push("<p>" + paragraphBuffer.join("<br>") + "</p>");
        paragraphBuffer = [];
      }
    }
    function closeLists() {
      if (inUl) { html.push("</ul>"); inUl = false; }
      if (inOl) { html.push("</ol>"); inOl = false; }
    }
    function inline(s) {
      // 行内：加粗 **x** / 行内代码 `x` / 链接 [t](u)
      return s
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    }

    lines.forEach(function (raw) {
      var line = raw.replace(/\s+$/, "");
      if (!line) { flushParagraph(); closeLists(); return; }

      // 标题（注意转义后 # 不变）
      var h1 = line.match(/^#\s+(.*)$/);
      var h2 = line.match(/^##\s+(.*)$/);
      var h3 = line.match(/^###\s+(.*)$/);
      if (h3) { flushParagraph(); closeLists(); html.push("<h3>" + inline(h3[1]) + "</h3>"); return; }
      if (h2) { flushParagraph(); closeLists(); html.push("<h2>" + inline(h2[1]) + "</h2>"); return; }
      if (h1) { flushParagraph(); closeLists(); html.push("<h1>" + inline(h1[1]) + "</h1>"); return; }

      // 无序列表
      var ul = line.match(/^[-*+]\s+(.*)$/);
      if (ul) { flushParagraph(); if (inOl) { html.push("</ol>"); inOl = false; } if (!inUl) { html.push("<ul>"); inUl = true; } html.push("<li>" + inline(ul[1]) + "</li>"); return; }

      // 有序列表
      var ol = line.match(/^\d+\.\s+(.*)$/);
      if (ol) { flushParagraph(); if (inUl) { html.push("</ul>"); inUl = false; } if (!inOl) { html.push("<ol>"); inOl = true; } html.push("<li>" + inline(ol[1]) + "</li>"); return; }

      // 引用
      var bq = line.match(/^&gt;\s?(.*)$/);
      if (bq) { flushParagraph(); closeLists(); html.push("<blockquote style=\"border-left:3px solid #6366f1;padding-left:12px;color:#6b7280;margin:0 0 12px;\">" + inline(bq[1]) + "</blockquote>"); return; }

      // 水平线
      if (/^(---|\*\*\*|___)$/.test(line)) { flushParagraph(); closeLists(); html.push("<hr style=\"border:none;border-top:1px solid #e5e7eb;margin:16px 0;\" />"); return; }

      // 普通段落
      paragraphBuffer.push(inline(line));
    });
    flushParagraph();
    closeLists();
    return html.join("");
  }

  /** 构建评分 meta 行（score pill + word count + 关键词） */
  function buildMetaRow(data) {
    var score = extractScore(data.seo_score);
    var parts = [];
    if (score != null) {
      parts.push('<span class="score-pill ' + scoreClass(score) + '">📊 SEO Score: ' + score + '/100</span>');
    }
    if (data.word_count != null) {
      parts.push('<span class="word-count">' + data.word_count + ' words</span>');
    }
    if (data.primary_keyword || (data.keywords && data.keywords.primary_keyword)) {
      var kw = data.primary_keyword || data.keywords.primary_keyword;
      parts.push('<span class="word-count">🔑 ' + escapeHtml(kw) + '</span>');
    }
    if (data.lang) {
      parts.push('<span class="word-count">' + escapeHtml(data.lang === "zh" ? "中文" : "EN") + '</span>');
    }
    return '<div class="meta-row">' + parts.join("") + "</div>";
  }

  /** 构建建议列表 */
  function buildSuggestions(seoScore) {
    var sugg = extractSuggestions(seoScore);
    if (!sugg.length) return "";
    var items = sugg.map(function (s) { return "<li>" + escapeHtml(s) + "</li>"; }).join("");
    return '<div style="margin-top:16px;padding:14px 16px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;">' +
      '<div style="font-weight:600;font-size:13px;color:#b45309;margin-bottom:6px;">💡 Optimization suggestions</div>' +
      '<ul style="margin:0;padding-left:18px;font-size:13px;color:#92400e;">' + items + "</ul></div>";
  }

  function showError(container, message) {
    var el = document.createElement("div");
    el.className = "alert alert-error";
    el.textContent = message || "Something went wrong. Please try again.";
    container.innerHTML = "";
    container.appendChild(el);
  }

  function setButtonLoading(btn, loading, originalText) {
    if (!btn) return;
    if (loading) {
      btn.dataset.originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Generating…';
    } else {
      btn.disabled = false;
      btn.innerHTML = originalText || btn.dataset.originalText || btn.innerHTML;
    }
  }

  /* ---------- 模块：Demo 表单（index.html） ---------- */
  function initDemoForm() {
    var form = document.getElementById("demo-form");
    if (!form) return;
    var resultBox = document.getElementById("demo-result");
    var submitBtn = document.getElementById("demo-submit");
    var originalLabel = submitBtn ? submitBtn.innerHTML : "Generate Sample";

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var keywordEl = document.getElementById("demo-keyword");
      var langEl = document.getElementById("demo-lang");
      var keyword = (keywordEl && keywordEl.value || "").trim();
      var lang = (langEl && langEl.value) || "en";

      if (!keyword) {
        showError(resultBox, "Please enter a keyword.");
        return;
      }

      setButtonLoading(submitBtn, true, originalLabel);
      // 清空并显示加载态（用 textContent 写提示，安全）
      resultBox.innerHTML = "";
      var loading = document.createElement("div");
      loading.className = "demo-result-empty";
      var sp = document.createElement("span");
      sp.className = "spinner";
      var txt = document.createElement("div");
      txt.textContent = "Generating sample article for \"" + keyword + "\"…";
      txt.style.color = "var(--color-text)";
      loading.appendChild(sp);
      loading.appendChild(txt);
      resultBox.appendChild(loading);

      postJSON("/api/demo", { keyword: keyword, lang: lang })
        .then(function (data) {
          renderDemoResult(resultBox, data, keyword, lang);
        })
        .catch(function (err) {
          showError(resultBox, err.message || "Failed to generate sample. Please try again later.");
        })
        .then(function () {
          setButtonLoading(submitBtn, false, originalLabel);
        });
    });
  }

  function renderDemoResult(container, data, keyword, lang) {
    container.innerHTML = "";
    var wrap = document.createElement("div");
    wrap.className = "article-preview";

    var metaHtml = buildMetaRow({
      seo_score: data.seo_score,
      word_count: data.word_count,
      primary_keyword: data.primary_keyword || (data.keywords && data.keywords.primary_keyword) || keyword,
      lang: data.lang || lang
    });

    var bodyHtml;
    if (data.body_markdown) {
      bodyHtml = renderMarkdown(data.body_markdown);
    } else if (data.title) {
      bodyHtml = "<h1>" + escapeHtml(data.title) + "</h1><p>" + escapeHtml(data.meta_description || "") + "</p>";
    } else {
      bodyHtml = "<p>" + escapeHtml(JSON.stringify(data)) + "</p>";
    }

    // 用 innerHTML 注入的是经过 escape + 受控转换的 HTML（无原始用户内容）
    wrap.innerHTML = metaHtml + bodyHtml + buildSuggestions(data.seo_score);

    var note = document.createElement("p");
    note.style.cssText = "font-size:13px;color:var(--color-text-muted);margin-top:16px;border-top:1px solid var(--color-border);padding-top:14px;";
    note.textContent = "This is a sample preview (first ~500 words). Purchase an article to get the full 1500+ word version with complete SEO score.";

    container.appendChild(wrap);
    container.appendChild(note);
  }

  /* ---------- 模块：PayPal 按钮（index.html pricing 区） ---------- */

  /** 套餐配置：plan 标识、类型（order/subscription）、金额、描述 */
  var PLANS = {
    single: { type: "order", amount: "2.00", label: "Single Article ($2)" },
    starter: { type: "subscription", amount: "29.00", label: "Starter ($29/mo)" },
    pro: { type: "subscription", amount: "79.00", label: "Pro ($79/mo)" }
  };

  function initPayPalButtons() {
    var hasAny = ["single", "starter", "pro"].some(function (p) {
      return document.getElementById("paypal-button-" + p);
    });
    if (!hasAny) return;

    function showPayPalFallback(plan, reason) {
      var el = document.getElementById("paypal-button-" + plan);
      if (!el) return;
      el.innerHTML = "";
      var ph = document.createElement("div");
      ph.className = "paypal-placeholder";
      ph.textContent = reason || "PayPal unavailable (sandbox).";
      el.appendChild(ph);
    }

    function waitForPayPal(timeoutMs) {
      return new Promise(function (resolve, reject) {
        var start = Date.now();
        (function check() {
          if (window.paypal && typeof window.paypal.Buttons === "function") {
            return resolve(window.paypal);
          }
          if (window.__PAYPAL_SDK_FAILED) {
            return reject(new Error("PayPal SDK failed to load"));
          }
          if (Date.now() - start > timeoutMs) {
            return reject(new Error("PayPal SDK load timeout"));
          }
          setTimeout(check, 150);
        })();
      });
    }

    waitForPayPal(8000)
      .then(function (paypal) {
        Object.keys(PLANS).forEach(function (plan) {
          var containerId = "#paypal-button-" + plan;
          var containerEl = document.getElementById("paypal-button-" + plan);
          if (!containerEl) return;
          containerEl.innerHTML = ""; // 清除占位

          var cfg = PLANS[plan];

          var buttonConfig = {
            style: { layout: "vertical", color: "blue", shape: "pill", label: "pay" },
            onApprove: function (data) {
              // 订阅返回 subscription_id；一次性订单返回 orderID
              var captureUrl = cfg.type === "subscription"
                ? "/api/paypal/activate-subscription"
                : "/api/paypal/capture";
              var captureBody = cfg.type === "subscription"
                ? { subscription_id: data.subscriptionID, plan: plan }
                : { order_id: data.orderID, plan: plan };

              return postJSON(captureUrl, captureBody).then(function (resp) {
                var orderId = (resp && (resp.order_id || resp.subscription_id)) ||
                              data.orderID || data.subscriptionID || "";
                var qs = orderId ? ("?order_id=" + encodeURIComponent(orderId) +
                                    "&plan=" + encodeURIComponent(plan)) : "?plan=" + encodeURIComponent(plan);
                window.location.href = "/thank-you.html" + qs;
              }).catch(function (err) {
                // 捕获失败仍跳转（带错误标记），避免用户卡住
                console.error("PayPal capture error:", err);
                window.location.href = "/thank-you.html?plan=" + encodeURIComponent(plan) + "&error=" + encodeURIComponent(err.message || "capture_failed");
              });
            },
            onError: function (err) {
              console.error("PayPal button error:", err);
            }
          };

          if (cfg.type === "subscription") {
            // 订阅按钮：服务端创建订阅并返回 subscription_id
            buttonConfig.createSubscription = function (_data, actions) {
              return postJSON("/api/paypal/create-subscription", { plan: plan })
                .then(function (resp) { return resp.subscription_id; });
            };
          } else {
            // 一次性按篇按钮：服务端创建订单并返回 order_id
            buttonConfig.createOrder = function (_data, _actions) {
              return postJSON("/api/paypal/create-order", { plan: plan, amount: cfg.amount })
                .then(function (resp) { return resp.order_id; });
            };
          }

          try {
            paypal.Buttons(buttonConfig).render(containerId);
          } catch (e) {
            showPayPalFallback(plan, "PayPal render error.");
          }
        });
      })
      .catch(function () {
        Object.keys(PLANS).forEach(function (plan) {
          showPayPalFallback(plan, "PayPal unavailable (sandbox).");
        });
      });
  }

  /* ---------- 模块：thank-you.html 文章生成 ---------- */
  function initArticleGenerator() {
    var form = document.getElementById("article-form");
    if (!form) return; // 不在 thank-you 页

    var resultBox = document.getElementById("article-result");
    var submitBtn = document.getElementById("article-submit");
    var originalLabel = submitBtn ? submitBtn.innerHTML : "Generate My Article";

    // 显示 order_id / plan / error
    var orderId = getQueryParam("order_id");
    var plan = getQueryParam("plan");
    var errorParam = getQueryParam("error");
    var orderIdDisplay = document.getElementById("order-id-display");
    var orderAlert = document.getElementById("order-alert");

    if (orderIdDisplay) {
      var segs = [];
      if (plan) segs.push("Plan: " + plan);
      if (orderId) segs.push("Order ID: " + orderId);
      if (segs.length) orderIdDisplay.textContent = segs.join(" · ");
    }
    if (orderAlert && errorParam) {
      var warn = document.createElement("div");
      warn.className = "alert alert-error";
      warn.textContent = "Payment verification issue: " + errorParam + ". If you believe this is an error, contact support.";
      orderAlert.appendChild(warn);
    } else if (orderAlert && orderId) {
      var ok = document.createElement("div");
      ok.className = "alert alert-info";
      ok.textContent = "✓ Payment confirmed. You may now generate your article.";
      orderAlert.appendChild(ok);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var keywordEl = document.getElementById("article-keyword");
      var langEl = document.getElementById("article-lang");
      var keyword = (keywordEl && keywordEl.value || "").trim();
      var lang = (langEl && langEl.value) || "en";

      if (!keyword) {
        showError(resultBox, "Please enter a keyword.");
        return;
      }

      setButtonLoading(submitBtn, true, originalLabel);
      resultBox.innerHTML = "";
      var loading = document.createElement("div");
      loading.className = "result-empty";
      var sp = document.createElement("span");
      sp.className = "spinner";
      var txt = document.createElement("div");
      txt.textContent = "Generating your full article…";
      txt.style.color = "var(--color-text)";
      loading.appendChild(sp);
      loading.appendChild(txt);
      resultBox.appendChild(loading);

      postJSON("/api/paypal/generate-article", {
        order_id: orderId,
        plan: plan,
        keyword: keyword,
        lang: lang
      })
        .then(function (data) {
          renderArticleResult(resultBox, data, keyword, lang);
        })
        .catch(function (err) {
          showError(resultBox, err.message || "Failed to generate article. Please try again.");
        })
        .then(function () {
          setButtonLoading(submitBtn, false, originalLabel);
        });
    });
  }

  function renderArticleResult(container, data, keyword, lang) {
    container.innerHTML = "";
    var wrap = document.createElement("div");
    wrap.className = "article-preview";

    var metaHtml = buildMetaRow({
      seo_score: data.seo_score,
      word_count: data.word_count,
      primary_keyword: data.primary_keyword || (data.keywords && data.keywords.primary_keyword) || keyword,
      lang: data.lang || lang
    });

    var bodyHtml = data.body_markdown
      ? renderMarkdown(data.body_markdown)
      : "<p>" + escapeHtml(JSON.stringify(data)) + "</p>";

    wrap.innerHTML = metaHtml + bodyHtml + buildSuggestions(data.seo_score);
    container.appendChild(wrap);

    // 下载 .md 文件（客户端 Blob 生成，无需服务端）
    var actions = document.createElement("div");
    actions.className = "article-actions";

    var dlBtn = document.createElement("button");
    dlBtn.className = "btn btn-primary";
    dlBtn.type = "button";
    dlBtn.textContent = "⬇ Download Markdown (.md)";
    dlBtn.addEventListener("click", function () {
      var md = buildMarkdownFile(data, keyword, lang);
      var blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      var safeName = (keyword || "article").replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase() || "article";
      a.download = safeName + ".md";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
    actions.appendChild(dlBtn);

    if (data.seo_score != null) {
      var score = extractScore(data.seo_score);
      if (score != null) {
        var scoreBtn = document.createElement("button");
        scoreBtn.className = "btn btn-green";
        scoreBtn.type = "button";
        scoreBtn.textContent = "📊 Score: " + score + "/100";
        actions.appendChild(scoreBtn);
      }
    }

    container.appendChild(actions);
  }

  /** 拼装可下载的 Markdown 文件内容（含 YAML frontmatter） */
  function buildMarkdownFile(data, keyword, lang) {
    var title = data.title || (data.keywords && data.keywords.primary_keyword) || keyword || "SEO Article";
    var meta = data.meta_description || "";
    var body = data.body_markdown || "";
    var score = extractScore(data.seo_score);
    var kw = data.primary_keyword || (data.keywords && data.keywords.primary_keyword) || keyword;

    var front = "---\n";
    front += "title: " + String(title).replace(/\n/g, " ") + "\n";
    front += "description: " + String(meta).replace(/\n/g, " ") + "\n";
    if (kw) front += "keywords: " + String(kw).replace(/\n/g, " ") + "\n";
    if (lang) front += "lang: " + lang + "\n";
    if (score != null) front += "seo_score: " + score + "\n";
    if (data.word_count != null) front += "word_count: " + data.word_count + "\n";
    front += "generated_by: SEO Content Generator (AutoCorp)\n";
    front += "date: " + new Date().toISOString() + "\n";
    front += "---\n\n";

    return front + body;
  }

  /* ---------- 启动 ---------- */
  function domReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  domReady(function () {
    initDemoForm();          // index.html
    initPayPalButtons();     // index.html
    initArticleGenerator();  // thank-you.html
  });

})();
