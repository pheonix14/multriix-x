/**
 * NeuralDesk — chat.js
 * Chat logic: WebSocket streaming, sessions, message rendering
 */

const Chat = (() => {
  let ws = null;
  let currentSessionId = 'default';
  let currentAIBubble = null;
  let currentAIText = '';
  let isStreaming = false;
  let autoScroll = true;
  let tokenCount = 0;
  let startTime = 0;

  function init() {
    const textarea = Utils.el('chat-textarea');
    const sendBtn  = Utils.el('chat-send-btn');

    // Auto-resize textarea
    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
      sendBtn.disabled = !textarea.value.trim();

      const len = textarea.value.length;
      Utils.setText('char-count', len > 500 ? `${len}/16000` : '');
    });

    // Enter to send
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled && !isStreaming) send();
      }
    });

    // Detect manual scroll up
    const messages = Utils.el('chat-messages');
    messages.addEventListener('scroll', () => {
      const atBottom = messages.scrollHeight - messages.scrollTop - messages.clientHeight < 50;
      autoScroll = atBottom;
    });

    // Connect WS
    connectWS();
    loadSessions();
    newSession(false); // start fresh but don't create file until first message
  }

  function connectWS() {
    ws = API.ws('/ws/chat',
      (data) => handleWSMessage(data),
      () => Utils.toast('Chat connection lost — reconnecting…', 'warning')
    );
  }

  function handleWSMessage(data) {
    if (data.error) {
      finishStream();
      appendErrorBubble(data.error);
      return;
    }
    if (data.token) {
      if (!currentAIBubble) startAIBubble();
      currentAIText += data.token;
      currentAIBubble.querySelector('.bubble-content').textContent = currentAIText;
      if (autoScroll) scrollBottom();
    }
    if (data.done) {
      finishStream(data);
    }
  }

  function send() {
    const textarea = Utils.el('chat-textarea');
    const text = textarea.value.trim();
    if (!text || isStreaming) return;

    // Hide empty state
    Utils.hide('chat-empty');

    // Append user bubble
    appendUserBubble(text);
    textarea.value = '';
    textarea.style.height = 'auto';
    Utils.el('chat-send-btn').disabled = true;

    // Prepare streaming state
    isStreaming = true;
    tokenCount = 0;
    startTime = Date.now();
    currentAIText = '';
    currentAIBubble = null;

    // Get active model + config from App
    const cfg = window._appConfig || {};
    const chatCfg = cfg.chat || {};

    ws.send({
      message: text,
      model: window._activeModel || 'llama3.2:3b',
      session_id: currentSessionId,
      system: chatCfg.system_prompt || 'You are a helpful assistant.',
      temperature: chatCfg.temperature ?? 0.7,
      max_tokens: chatCfg.max_tokens ?? 2048,
      use_gpu: chatCfg.use_gpu !== false,
    });

    // Show stop button
    Utils.el('chat-send-btn').innerHTML = '■';
    Utils.el('chat-send-btn').disabled = false;
    Utils.el('chat-send-btn').onclick = stopStreaming;

    scrollBottom();
  }

  function stopStreaming() {
    ws.close();
    setTimeout(connectWS, 100);
    finishStream();
  }

  function startAIBubble() {
    const group = document.createElement('div');
    group.className = 'message-group ai';
    group.innerHTML = `
      <div class="message-meta">[AI] · <span class="ts">now</span></div>
      <div class="message-bubble">
        <div class="bubble-content cursor-blink"></div>
        <div class="msg-stats hidden" id="msg-stats-${Date.now()}">
          <span>~ <span class="tps-val">—</span> tok/s</span>
          <span>| <span class="tok-val">0</span> tokens</span>
        </div>
      </div>`;
    Utils.el('chat-messages').appendChild(group);
    currentAIBubble = group;
    scrollBottom();
  }

  function finishStream(data) {
    isStreaming = false;
    if (currentAIBubble) {
      const content = currentAIBubble.querySelector('.bubble-content');
      content.classList.remove('cursor-blink');
      content.innerHTML = Utils.renderMarkdown(currentAIText);

      // Show stats
      const elapsed = (Date.now() - startTime) / 1000;
      const tps = elapsed > 0 ? (currentAIText.length / 5 / elapsed).toFixed(1) : '—';
      const statsEl = currentAIBubble.querySelector('[id^="msg-stats-"]');
      if (statsEl && window._appConfig?.ui?.show_speed) {
        statsEl.classList.remove('hidden');
        statsEl.querySelector('.tps-val').textContent = tps;
        statsEl.querySelector('.tok-val').textContent = Math.round(currentAIText.length / 4);
      }
      currentAIBubble = null;
    }
    // Reset send button
    const sendBtn = Utils.el('chat-send-btn');
    sendBtn.innerHTML = '➤';
    sendBtn.onclick = send;
    sendBtn.disabled = !Utils.el('chat-textarea').value.trim();
    scrollBottom();
  }

  function appendUserBubble(text) {
    const group = document.createElement('div');
    group.className = 'message-group user';
    const time = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    group.innerHTML = `
      <div class="message-meta">You · ${time}</div>
      <div class="message-bubble">${text.replace(/</g,'&lt;')}</div>`;
    Utils.el('chat-messages').appendChild(group);
  }

  function appendErrorBubble(error) {
    const group = document.createElement('div');
    group.className = 'message-group ai';
    group.innerHTML = `
      <div class="message-bubble" style="border-color:var(--danger); color:var(--danger);">
        [Error]: ${error}
      </div>`;
    Utils.el('chat-messages').appendChild(group);
    scrollBottom();
  }

  function scrollBottom() {
    const msgs = Utils.el('chat-messages');
    msgs.scrollTop = msgs.scrollHeight;
  }

  // ── SESSIONS ────────────────────────────────────────────────
  async function loadSessions() {
    try {
      const sessions = await API.sessions.list();
      const sel = Utils.el('session-select');
      sel.innerHTML = sessions.map(s =>
        `<option value="${s.id}">${Utils.truncate(s.title, 30)}</option>`
      ).join('') || '<option value="default">New Chat</option>';
      if (sessions.length) currentSessionId = sessions[0].id;
    } catch (e) {
      console.error('Sessions load failed', e);
    }
  }

  async function loadSession(id) {
    currentSessionId = id;
    Utils.el('chat-messages').innerHTML = '';
    Utils.show('chat-empty');
    try {
      const data = await API.sessions.get(id);
      const messages = data.messages || [];
      if (messages.length) {
        Utils.hide('chat-empty');
        messages.forEach(m => {
          if (m.role === 'user') appendUserBubble(m.content);
          else {
            const group = document.createElement('div');
            group.className = 'message-group ai';
            group.innerHTML = `<div class="message-meta">[AI]</div>
              <div class="message-bubble"><div class="bubble-content">${Utils.renderMarkdown(m.content)}</div></div>`;
            Utils.el('chat-messages').appendChild(group);
          }
        });
        scrollBottom();
      }
    } catch (e) { console.error(e); }
  }

  function newSession(createFile = true) {
    const id = 'sess_' + Date.now().toString(36);
    currentSessionId = id;
    Utils.el('chat-messages').innerHTML = '';
    Utils.show('chat-empty');

    const sel = Utils.el('session-select');
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = 'New Chat';
    opt.selected = true;
    sel.insertBefore(opt, sel.firstChild);
  }

  async function deleteSession() {
    if (!confirm('Delete this chat? This cannot be undone.')) return;
    try {
      await API.sessions.delete(currentSessionId);
      Utils.toast('Chat deleted', 'success');
      await loadSessions();
      newSession(false);
    } catch (e) { Utils.toast('Delete failed: ' + e.message, 'error'); }
  }

  function exportSession() {
    const messages = Utils.el('chat-messages').querySelectorAll('.message-group');
    let txt = `=== NeuralDesk Chat Export ===\n\n`;
    messages.forEach(m => {
      const isUser = m.classList.contains('user');
      const content = m.querySelector('.bubble-content')?.textContent || m.querySelector('.message-bubble')?.textContent || '';
      txt += `[${isUser ? 'You' : 'AI'}]: ${content.trim()}\n\n`;
    });
    const blob = new Blob([txt], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `chat-${currentSessionId}.txt`;
    a.click();
  }

  function changeModel(name) {
    if (window.Models && typeof Models.setActive === 'function') {
      Models.setActive(name);
    }
  }

  return { init, send, newSession, loadSession, deleteSession, exportSession, changeModel };
})();

window.Chat = Chat;
