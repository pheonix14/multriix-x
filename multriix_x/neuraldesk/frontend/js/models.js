/**
 * NeuralDesk — models.js
 * Model selector, status display, pull progress, delete
 */

const Models = (() => {
  let allModels = [];
  let searchQuery = '';

  async function init() {
    await refresh();
  }

  async function refresh() {
    Utils.el('model-grid').innerHTML = [1,2,3].map(() =>
      `<div class="card card-pad skeleton" style="height:160px;"></div>`
    ).join('');

    try {
      const data = await API.models.list();
      allModels = data.models || [];

      Utils.setText('model-count', `${allModels.length} model${allModels.length !== 1 ? 's' : ''} installed`);

      // Update model dropdown in topbar
      // Update model dropdown in topbar
      updateActiveModelBadge();
      
      // Update chat select dropdown
      const chatSel = Utils.el('chat-model-select');
      if (chatSel) {
        const options = allModels.map(m => 
          `<option value="${m.name}" ${m.name === window._activeModel ? 'selected' : ''}>${m.name}</option>`
        );
        options.unshift(`<option value="ALL_AI_MODE" ${window._activeModel === 'ALL_AI_MODE' ? 'selected' : ''}>🌐 ALL AI (Ensemble)</option>`);
        chatSel.innerHTML = options.join('');
      }

      render();

      // Update Ollama status
      const dot = Utils.el('ollama-dot');
      const stat = Utils.el('stat-ollama');
      if (data.online) {
        dot.style.background = 'var(--success)';
        stat.textContent = 'Ollama Online';
      } else {
        dot.style.background = 'var(--danger)';
        stat.textContent = 'Ollama Offline';
      }
    } catch (e) {
      Utils.el('model-grid').innerHTML = `<div class="text-secondary text-sm" style="padding:var(--sp-5);">
        [x] Could not load models: ${e.message}</div>`;
    }
  }

  function render() {
    const filtered = allModels.filter(m =>
      !searchQuery || m.name.toLowerCase().includes(searchQuery)
    );

    if (!filtered.length) {
      Utils.el('model-grid').innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:var(--sp-10); color:var(--text-secondary);">
        <div style="font-size:48px; opacity:0.3; margin-bottom:var(--sp-3); font-family:var(--font-mono)">[ / ]</div>
        <p>No models found. Download one above!</p>
      </div>`;
      return;
    }

    Utils.el('model-grid').innerHTML = filtered.map(m => modelCard(m)).join('');
  }

  function modelCard(m) {
    const isActive = m.name === (window._activeModel || '');
    const sizeGB = m.size ? (m.size / 1e9).toFixed(1) : '?';
    return `
    <div class="card card-pad" id="model-card-${m.name.replace(/[:.]/g,'_')}" style="${isActive ? 'border-color:var(--accent); box-shadow: 0 0 0 2px var(--accent-light);' : ''}">
      <div class="flex items-center justify-between" style="margin-bottom:var(--sp-3);">
        <div style="font-family:var(--font-mono); font-size:var(--text-base); font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:70%;">${m.name}</div>
        <span class="badge ${isActive ? 'badge-success' : 'badge-gray'}">${isActive ? '● Active' : '○ Available'}</span>
      </div>
      <div class="flex gap-2" style="flex-wrap:wrap; margin-bottom:var(--sp-4);">
        ${m.family ? `<span class="badge badge-info">${m.family}</span>` : ''}
        ${m.parameters ? `<span class="badge badge-gray">${m.parameters}</span>` : ''}
        <span class="badge badge-gray">Size: ${sizeGB} GB</span>
      </div>
      ${m.modified ? `<div class="text-xs text-secondary" style="margin-bottom:var(--sp-3);">Updated ${Utils.timeAgo(new Date(m.modified).getTime()/1000)}</div>` : ''}
      <div class="flex gap-2">
        <button class="btn btn-sm btn-primary" style="flex:1;" onclick="Models.setActive('${m.name}')">
          ${isActive ? 'Active' : 'Use This Model'}
        </button>
        <button class="btn btn-sm btn-ghost" onclick="Models.showInfo('${m.name}')" title="Info">i</button>
        <button class="btn btn-sm btn-ghost" onclick="Models.confirmDelete('${m.name}')" title="Delete" style="color:var(--danger)">x</button>
      </div>
    </div>`;
  }

  function filter() {
    searchQuery = Utils.el('model-search').value.toLowerCase();
    render();
  }

  function setActive(name) {
    window._activeModel = name;
    Utils.setText('active-model-name', name);
    Utils.setText('chip-model-name', name);
    Utils.el('chip-status-dot').className = 'status-dot-inline status-online';
    Utils.setText('chip-status-text', 'Ready');

    const chatSel = Utils.el('chat-model-select');
    if (chatSel) {
      chatSel.value = name;
    }

    // Update config
    if (window._appConfig) window._appConfig.active_model = name;
    API.config.save({ ...window._appConfig, active_model: name }).catch(() => {});

    render(); // Re-render to update active badge
    Utils.toast(`Now using: ${name}`, 'success');
  }

  function updateActiveModelBadge() {
    if (!window._activeModel && allModels.length) {
      window._activeModel = window._appConfig?.active_model || allModels[0].name;
    }
    if (window._activeModel) {
      Utils.setText('active-model-name', window._activeModel);
      Utils.setText('chip-model-name', window._activeModel);
      const chatSel = Utils.el('chat-model-select');
      if (chatSel) {
        chatSel.value = window._activeModel;
      }
    }
  }

  async function pull() {
    const name = Utils.el('pull-model-input').value.trim();
    if (!name) { Utils.toast('Enter a model name first', 'warning'); return; }

    Utils.show('pull-progress');
    Utils.setText('pull-status', `Downloading ${name}…`);
    Utils.el('pull-bar').style.width = '0%';
    Utils.setText('pull-pct', '0%');

    try {
      const response = await fetch('/api/models/pull', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        for (let line of lines) {
          if (!line.trim()) continue;
          const data = JSON.parse(line);
          if (data.error) throw new Error(data.error);
          
          Utils.setText('pull-status', data.status);
          if (data.total && data.completed) {
            const pct = Math.round((data.completed / data.total) * 100);
            Utils.el('pull-bar').style.width = pct + '%';
            Utils.setText('pull-pct', pct + '%');
          }
        }
      }

      Utils.el('pull-bar').style.width = '100%';
      Utils.setText('pull-pct', '100%');
      Utils.setText('pull-status', `[+] ${name} downloaded!`);
      Utils.el('pull-model-input').value = '';
      Utils.toast(`${name} is ready to use!`, 'success');
      setTimeout(() => { Utils.hide('pull-progress'); refresh(); }, 2000);
    } catch (e) {
      Utils.el('pull-bar').style.width = '0%';
      Utils.setText('pull-status', `[x] Failed: ${e.message}`);
      Utils.toast(`Download failed: ${e.message}`, 'error');
    }
  }

  async function confirmDelete(name) {
    if (!confirm(`Delete "${name}"? It will need to be re-downloaded to use it again.`)) return;
    try {
      await API.models.delete(name);
      if (window._activeModel === name) {
        window._activeModel = '';
        Utils.setText('active-model-name', 'None');
      }
      Utils.toast(`${name} deleted`, 'success');
      refresh();
    } catch (e) {
      Utils.toast(`Delete failed: ${e.message}`, 'error');
    }
  }

  async function showInfo(name) {
    try {
      const info = await API.models.info(name);
      alert(JSON.stringify(info, null, 2));
    } catch (e) {
      Utils.toast('Could not load model info', 'error');
    }
  }

  function openPicker() {
    App.switchView('models');
  }

  return { init, refresh, filter, setActive, pull, confirmDelete, showInfo, openPicker };
})();

window.Models = Models;
