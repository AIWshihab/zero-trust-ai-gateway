// Zero Trust AI Gateway — Request Interceptor
// Runs in MAIN world so it can hook window.fetch and XMLHttpRequest.
// Communicates with the isolated content script via window.postMessage.

(function () {
  'use strict';

  const AI_ENDPOINTS = [
    /api\.openai\.com/i,
    /api\.anthropic\.com/i,
    /api\.cohere\.ai/i,
    /api\.together\.xyz/i,
    /generativelanguage\.googleapis\.com/i,
    /api-inference\.huggingface\.co/i,
    /api\.groq\.com/i,
    /api\.mistral\.ai/i,
    /api\.perplexity\.ai/i,
    /api\.replicate\.com/i,
    /api\.together\.ai/i,
    /openrouter\.ai\/api/i,
  ];

  function isAIEndpoint(url) {
    try { return AI_ENDPOINTS.some(r => r.test(String(url))); } catch { return false; }
  }

  function extractPrompt(body) {
    if (!body || typeof body !== 'string') return '';
    try {
      const parsed = JSON.parse(body);
      // OpenAI / Anthropic messages format
      if (Array.isArray(parsed.messages)) {
        const last = [...parsed.messages].reverse().find(m => m.content);
        if (typeof last?.content === 'string') return last.content.slice(0, 2000);
        if (Array.isArray(last?.content)) {
          const txt = last.content.find(c => c.type === 'text');
          if (txt?.text) return String(txt.text).slice(0, 2000);
        }
      }
      // Generic prompt field
      if (typeof parsed.prompt === 'string') return parsed.prompt.slice(0, 2000);
      if (typeof parsed.inputs === 'string') return parsed.inputs.slice(0, 2000);
    } catch { /* ignore */ }
    return String(body).slice(0, 500);
  }

  let reqCounter = 0;
  const pendingRequests = new Map();

  // Listen for gateway decisions coming back from the content script
  window.addEventListener('message', function (event) {
    if (event.source !== window) return;
    if (event.data?.type !== 'ZTA_GATEWAY_DECISION') return;
    const { requestId, decision, reason } = event.data;
    const pending = pendingRequests.get(requestId);
    if (!pending) return;
    pendingRequests.delete(requestId);
    if (decision === 'block') {
      pending.reject(new Error('[Zero Trust Gateway] Blocked: ' + (reason || 'Policy violation')));
    } else {
      pending.resolve(decision || 'allow');
    }
  });

  function checkWithGateway(url, method, body) {
    const requestId = ++reqCounter;
    const extractedPrompt = extractPrompt(body);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pendingRequests.delete(requestId);
        resolve('allow'); // fail open — never break the user's workflow
      }, 5000);

      pendingRequests.set(requestId, {
        resolve: (v) => { clearTimeout(timeout); resolve(v); },
        reject:  (e) => { clearTimeout(timeout); reject(e); },
      });

      window.postMessage({
        type: 'ZTA_CHECK_AI_REQUEST',
        requestId,
        url: String(url),
        method: method || 'POST',
        extractedPrompt,
      }, '*');
    });
  }

  // ── Hook window.fetch ────────────────────────────────────────────────────────
  const originalFetch = window.fetch;
  window.fetch = async function (input, init) {
    const url = input instanceof Request ? input.url : String(input || '');
    if (isAIEndpoint(url)) {
      let body = init?.body;
      if (!body && input instanceof Request) {
        try { const clone = input.clone(); body = await clone.text(); } catch { /* skip */ }
      }
      try {
        await checkWithGateway(url, init?.method || 'POST', typeof body === 'string' ? body : '');
      } catch (err) {
        window.dispatchEvent(new CustomEvent('ZTA_REQUEST_BLOCKED', { detail: { url, reason: String(err.message) } }));
        return new Response(
          JSON.stringify({ error: { type: 'zero_trust_block', message: String(err.message), code: 'policy_violation' } }),
          { status: 403, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }
    return originalFetch.apply(this, arguments);
  };

  // ── Hook XMLHttpRequest ──────────────────────────────────────────────────────
  const OrigXHR = window.XMLHttpRequest;
  function ZTAXMLHttpRequest() {
    const xhr = new OrigXHR();
    let _url = '', _method = 'GET';

    const origOpen = xhr.open.bind(xhr);
    xhr.open = function (method, url) {
      _url = String(url || '');
      _method = String(method || 'GET');
      return origOpen.apply(xhr, arguments);
    };

    const origSend = xhr.send.bind(xhr);
    xhr.send = function (body) {
      if (!isAIEndpoint(_url)) { return origSend.apply(xhr, arguments); }

      const bodyStr = (typeof body === 'string') ? body : '';
      checkWithGateway(_url, _method, bodyStr)
        .then(() => origSend.apply(xhr, arguments))
        .catch(err => {
          window.dispatchEvent(new CustomEvent('ZTA_REQUEST_BLOCKED', { detail: { url: _url, reason: String(err.message) } }));
          Object.defineProperty(xhr, 'status', { get: () => 403, configurable: true });
          Object.defineProperty(xhr, 'responseText', {
            get: () => JSON.stringify({ error: { type: 'zero_trust_block', message: String(err.message) } }),
            configurable: true,
          });
          xhr.dispatchEvent(new Event('load'));
          xhr.dispatchEvent(new Event('loadend'));
        });
    };
    return xhr;
  }
  ZTAXMLHttpRequest.prototype = OrigXHR.prototype;
  window.XMLHttpRequest = ZTAXMLHttpRequest;

})();
