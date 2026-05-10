/**
 * NeuralDesk — utils.js
 * Shared helpers: toasts, tooltips, markdown, formatting
 */

const Utils = (() => {

  // ── TOAST NOTIFICATIONS ─────────────────────────────────────
  function toast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    const icons = { success: '+', error: 'x', info: 'i', warning: '!' };
    el.innerHTML = `<span style="font-weight:bold;font-family:var(--font-mono)">[${icons[type] || '·'}]</span><span style="flex:1">${message}</span>
      <span class="toast-close" onclick="this.parentElement.remove()">✕</span>`;
    container.appendChild(el);
    setTimeout(() => el.style.opacity = '0', duration - 300);
    setTimeout(() => el.remove(), duration);
  }

  // ── SIMPLE MARKDOWN RENDERER ─────────────────────────────────
  function renderMarkdown(text) {
    if (!text) return '';
    let html = text
      // Code blocks
      .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const cleanLang = (lang || 'py').toLowerCase();
        return `<pre><code class="lang-${lang}">${escaped}</code><div class="code-actions"><button class="code-btn" onclick="Utils.copyText(this.parentElement.previousSibling.textContent)">Copy</button><button class="code-btn" onclick="if(window.Files){ Files.loadCodeSnippet(this.parentElement.previousSibling.textContent, 'app.${cleanLang}'); } else { Utils.toast('Editor not initialized yet', 'warning'); }">Open in Editor</button></div></pre>`;
      })
      // Inline code
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Headers
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      // Unordered list
      .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      // Newlines to paragraphs
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    return `<p>${html}</p>`;
  }

  // ── TEXT UTILITIES ───────────────────────────────────────────
  function copyText(text) {
    navigator.clipboard.writeText(text).then(() => toast('Copied!', 'success', 2000));
  }

  function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const gb = bytes / 1e9;
    if (gb >= 1) return gb.toFixed(1) + ' GB';
    const mb = bytes / 1e6;
    if (mb >= 1) return mb.toFixed(0) + ' MB';
    return (bytes / 1024).toFixed(0) + ' KB';
  }

  function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  }

  function timeAgo(ts) {
    if (!ts) return '';
    const diff = (Date.now() / 1000) - ts;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return new Date(ts * 1000).toLocaleDateString();
  }

  function truncate(str, n = 60) {
    return str && str.length > n ? str.slice(0, n) + '…' : str;
  }

  // ── DOM HELPERS ──────────────────────────────────────────────
  function el(id) { return document.getElementById(id); }

  function show(id) { const e = el(id); if (e) e.classList.remove('hidden'); }
  function hide(id) { const e = el(id); if (e) e.classList.add('hidden'); }

  function setHTML(id, html) { const e = el(id); if (e) e.innerHTML = html; }
  function setText(id, text) { const e = el(id); if (e) e.textContent = text; }

  // ── GAUGE HELPER ─────────────────────────────────────────────
  function updateGauge(fillId, pct) {
    const fill = document.getElementById(fillId);
    if (!fill) return;
    const circumference = 2 * Math.PI * 35; // r=35
    const offset = circumference - (pct / 100) * circumference;
    fill.style.strokeDasharray = circumference;
    fill.style.strokeDashoffset = offset;
    // Color based on usage
    fill.className = 'gauge-fill' + (pct > 85 ? ' danger' : pct > 70 ? ' warn' : '');
  }

  return { toast, renderMarkdown, copyText, formatBytes, formatUptime, timeAgo, truncate, el, show, hide, setHTML, setText, updateGauge };
})();

// Make copyText global for inline onclick handlers
window.Utils = Utils;
