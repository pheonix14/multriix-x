/**
 * NeuralDesk — config.js
 * Visual config editor: sliders, toggles, autosave
 */

const Config = (() => {
  let cfg = {};
  let saveTimer = null;

  const sliderSettings = [
    { key: 'chat.temperature',    label: '[+] Creativity Level',    help: 'Higher = more creative/random. Lower = more factual/strict.', min: 0, max: 2, step: 0.05, leftLabel: 'Strict', rightLabel: 'Creative' },
    { key: 'chat.top_p',          label: '[*] Answer Confidence',    help: 'Controls how many word choices the AI considers. Lower = more focused.', min: 0.1, max: 1, step: 0.05, leftLabel: 'Focused', rightLabel: 'Broad' },
    { key: 'chat.top_k',          label: '[O] Word Choice Focus',    help: 'Limits how many word options the AI picks from each time.', min: 1, max: 100, step: 1, leftLabel: '1', rightLabel: '100' },
    { key: 'chat.repeat_penalty', label: '[~] Avoid Repetition',     help: 'Higher values stop the AI from repeating the same phrases.', min: 0.5, max: 2, step: 0.05, leftLabel: 'Allow', rightLabel: 'Strict' },
    { key: 'chat.max_tokens',     label: '[>] Max Answer Length',    help: 'Maximum number of words the AI will write per response.', min: 64, max: 8192, step: 64, leftLabel: 'Short', rightLabel: 'Long' },
    { key: 'chat.context_window', label: '[M] Conversation Memory',  help: 'How many previous messages the AI remembers during a conversation.', min: 1024, max: 32768, step: 1024, leftLabel: 'Less', rightLabel: 'More' },
  ];

  const toggleSettings = [
    { key: 'chat.use_gpu',        label: '[GPU] Hardware Acceleration', help: 'Use Graphics Card for AI Generation. Turn off if it crashes.' },
    { key: 'ui.show_token_count', label: '[#] Show Token Count',     help: 'Display how many tokens were used in each response.' },
    { key: 'ui.show_speed',       label: '[~] Show Response Speed',  help: 'Show how fast the AI is generating (tokens per second).' },
    { key: 'ui.auto_scroll',      label: '[v] Auto-Scroll Chat',     help: 'Automatically scroll down as new text arrives.' },
    { key: 'ui.enter_to_send',    label: '[>] Enter Key Sends',       help: 'Press Enter to send. Turn off to use Shift+Enter instead.' },
    { key: 'ui.show_timestamps',  label: '[T] Show Timestamps',      help: 'Display the time next to each message.' },
  ];

  async function init() {
    try {
      cfg = await API.config.get();
      window._appConfig = cfg;
      render();
    } catch (e) {
      Utils.toast('Could not load settings', 'error');
    }
  }

  function render() {
    // System prompt
    const sp = Utils.el('cfg-system-prompt');
    if (sp) sp.value = cfg.chat?.system_prompt || '';

    // Sliders in response section
    const responseBody = Utils.el('response-body');
    if (responseBody) {
      responseBody.innerHTML = sliderSettings.map(s => sliderRow(s)).join('');
      // Add listeners
      sliderSettings.forEach(s => {
        const id = 'cfg_' + s.key.replace('.', '_');
        const slider = Utils.el(id);
        const val = Utils.el(id + '_val');
        if (!slider) return;
        slider.value = getNestedKey(cfg, s.key) ?? (s.min + s.max) / 2;
        val.textContent = slider.value;
        slider.addEventListener('input', () => {
          val.textContent = slider.value;
          setNestedKey(cfg, s.key, parseFloat(slider.value));
          scheduleSave();
        });
      });
    }

    // Toggles in chatui section
    const chatuiBody = Utils.el('chatui-body');
    if (chatuiBody) {
      chatuiBody.innerHTML = toggleSettings.map(s => toggleRow(s)).join('');
      toggleSettings.forEach(s => {
        const id = 'cfg_' + s.key.replace('.', '_');
        const toggle = Utils.el(id);
        if (!toggle) return;
        toggle.checked = getNestedKey(cfg, s.key) ?? true;
        toggle.addEventListener('change', () => {
          setNestedKey(cfg, s.key, toggle.checked);
          scheduleSave();
        });
      });
    }

    // Ollama URL
    const urlInput = Utils.el('cfg-ollama-url');
    if (urlInput) {
      urlInput.value = cfg.connection?.ollama_url || 'http://127.0.0.1:11434';
      urlInput.addEventListener('input', () => {
        setNestedKey(cfg, 'connection.ollama_url', urlInput.value);
        scheduleSave();
      });
    }

    // HuggingFace Token
    const hfInput = Utils.el('cfg-hf-token');
    if (hfInput) {
      hfInput.value = cfg.connection?.hf_token || '';
      hfInput.addEventListener('input', () => {
        setNestedKey(cfg, 'connection.hf_token', hfInput.value);
        scheduleSave();
      });
    }

    // Anthropic API Key (Claude)
    const antInput = Utils.el('cfg-anthropic-key');
    if (antInput) {
      antInput.value = cfg.connection?.anthropic_key || '';
      antInput.addEventListener('input', () => {
        setNestedKey(cfg, 'connection.anthropic_key', antInput.value);
        scheduleSave();
      });
    }

    // System prompt listener
    if (sp) {
      sp.addEventListener('input', () => {
        setNestedKey(cfg, 'chat.system_prompt', sp.value);
        scheduleSave();
      });
    }
  }

  async function saveHFToken() {
    const hfInput = Utils.el('cfg-hf-token');
    if (hfInput) {
      setNestedKey(cfg, 'connection.hf_token', hfInput.value);
      try {
        await API.config.save(cfg);
        Utils.toast('HuggingFace Token saved successfully!', 'success');
      } catch (e) {
        Utils.toast('Failed to save token', 'error');
      }
    }
  }

  async function saveAnthropicKey() {
    const antInput = Utils.el('cfg-anthropic-key');
    if (antInput) {
      setNestedKey(cfg, 'connection.anthropic_key', antInput.value);
      try {
        await API.config.save(cfg);
        Utils.toast('Anthropic API Key saved successfully!', 'success');
      } catch (e) {
        Utils.toast('Failed to save key', 'error');
      }
    }
  }

  function sliderRow(s) {
    const id = 'cfg_' + s.key.replace('.', '_');
    return `
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">${s.label}
          <span class="help-btn tooltip-wrap">?<span class="tooltip-box">${s.help}</span></span>
        </div>
      </div>
      <div class="setting-control">
        <div class="slider-wrap">
          <span class="slider-label">${s.leftLabel}</span>
          <input type="range" class="setting-slider" id="${id}" min="${s.min}" max="${s.max}" step="${s.step}" value="${s.min}">
          <span class="slider-label">${s.rightLabel}</span>
        </div>
        <div class="slider-value" id="${id}_val">—</div>
      </div>
    </div>`;
  }

  function toggleRow(s) {
    const id = 'cfg_' + s.key.replace('.', '_');
    return `
    <div class="setting-row">
      <div class="setting-info">
        <div class="setting-label">${s.label}
          <span class="help-btn tooltip-wrap">?<span class="tooltip-box">${s.help}</span></span>
        </div>
      </div>
      <div class="setting-control" style="justify-content:flex-end;">
        <label class="toggle">
          <input type="checkbox" id="${id}">
          <span class="toggle-track"></span>
        </label>
      </div>
    </div>`;
  }

  function scheduleSave() {
    const status = Utils.el('autosave-status');
    if (status) { status.textContent = '[+] Saving…'; status.className = 'autosave-status saving'; }
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      window._appConfig = cfg;
      try {
        await API.config.save(cfg);
        if (status) { status.textContent = '[+] All changes saved'; status.className = 'autosave-status'; }
      } catch (e) {
        if (status) { status.textContent = '[x] Save failed'; status.className = 'autosave-status'; status.style.color = 'var(--danger)'; }
      }
    }, 800);
  }

  async function resetAll() {
    if (!confirm('Reset ALL settings to factory defaults? This cannot be undone.')) return;
    try {
      cfg = await API.config.reset();
      window._appConfig = cfg;
      render();
      Utils.toast('Settings reset to defaults', 'success');
    } catch (e) { Utils.toast('Reset failed', 'error'); }
  }

  function resetField(key) {
    const defaults = { system_prompt: 'You are a helpful assistant.' };
    if (defaults[key] !== undefined) {
      setNestedKey(cfg, 'chat.' + key, defaults[key]);
      const el = Utils.el('cfg-system-prompt');
      if (el) el.value = defaults[key];
      scheduleSave();
    }
  }

  async function testConnection() {
    const url = Utils.el('cfg-ollama-url')?.value || 'http://127.0.0.1:11434';
    const result = Utils.el('connection-result');
    if (result) result.textContent = '…';
    const t = Date.now();
    try {
      const r = await fetch(url + '/api/tags', { signal: AbortSignal.timeout(3000) });
      const ms = Date.now() - t;
      if (result) { result.textContent = `[+] Connected (${ms}ms)`; result.className = 'connection-result ok'; }
    } catch (e) {
      if (result) { result.textContent = '[x] Not reachable'; result.className = 'connection-result fail'; }
    }
  }

  function toggleSection(id) {
    const sec = Utils.el('sec-' + id);
    if (sec) sec.classList.toggle('collapsed');
  }

  // ── Helpers ─────────────────────────────────────────────────
  function getNestedKey(obj, dotKey) {
    return dotKey.split('.').reduce((o, k) => o?.[k], obj);
  }
  function setNestedKey(obj, dotKey, val) {
    const keys = dotKey.split('.');
    const last = keys.pop();
    const target = keys.reduce((o, k) => o[k] ??= {}, obj);
    target[last] = val;
  }

  return { init, render, resetAll, resetField, testConnection, toggleSection, saveHFToken, saveAnthropicKey };
})();

window.Config = Config;
