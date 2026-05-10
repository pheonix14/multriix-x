/**
 * NeuralDesk — monitor.js
 * Live system stats via WebSocket, process table
 */

const Monitor = (() => {
  let ws = null;
  let cpuHistory = [];
  let ramHistory = [];
  let allProcs = [];
  let sortKey = 'cpu_percent';
  let sortDir = -1;

  function init() {
    connectWS();
  }

  function connectWS() {
    ws = API.ws('/ws/monitor', (data) => {
      updateCPU(data.cpu);
      updateRAM(data.ram);
      updateGPU(data.gpu);
      updateDisk(data.disk);
      updateStats(data);
    });
  }

  function updateCPU(cpu) {
    if (!cpu) return;
    const pct = Math.round(cpu.percent || 0);
    Utils.updateGauge('cpu-fill', pct);
    Utils.setText('cpu-val', pct + '%');
    Utils.setText('cpu-cores', (cpu.cores || '?') + ' cores / ' + (cpu.threads || '?') + ' threads');
    Utils.setText('cpu-freq', cpu.freq_mhz ? cpu.freq_mhz + ' MHz' : 'N/A');
    Utils.setText('stat-cpu', pct + '%');

    // Per-core bars
    if (cpu.per_core) {
      const container = Utils.el('core-bars');
      if (container && container.children.length !== cpu.per_core.length) {
        container.innerHTML = cpu.per_core.map((_, i) => `
          <div class="core-bar-wrap">
            <div class="core-bar-outer"><div class="core-bar-inner" id="core${i}" style="height:0%"></div></div>
            <div class="core-bar-label">${i}</div>
          </div>`).join('');
      }
      cpu.per_core.forEach((pct, i) => {
        const bar = document.getElementById('core' + i);
        if (bar) bar.style.height = Math.round(pct) + '%';
      });
    }

    // History
    cpuHistory.push(pct);
    if (cpuHistory.length > 60) cpuHistory.shift();
  }

  function updateRAM(ram) {
    if (!ram) return;
    const pct = Math.round(ram.percent || 0);
    Utils.updateGauge('ram-fill', pct);
    Utils.setText('ram-val', pct + '%');
    Utils.setText('ram-used', (ram.used_gb || 0) + ' GB');
    Utils.setText('ram-total', (ram.total_gb || 0) + ' GB');
    Utils.setText('ram-free', (ram.available_gb || 0) + ' GB');
    Utils.setText('stat-ram', (ram.used_gb || '?') + '/' + (ram.total_gb || '?') + 'GB');

    ramHistory.push(pct);
    if (ramHistory.length > 60) ramHistory.shift();
  }

  function updateGPU(gpu) {
    const content = Utils.el('gpu-content');
    if (!content) return;
    if (!gpu) {
      content.innerHTML = `<div class="no-gpu">No NVIDIA GPU detected<br><span class="text-xs text-secondary">CPU-only mode</span></div>`;
      return;
    }
    const vramPct = gpu.vram_total_gb > 0 ? Math.round((gpu.vram_used_gb / gpu.vram_total_gb) * 100) : 0;
    content.innerHTML = `
      <div class="gauge-detail-row" style="margin-bottom:8px;"><span class="gauge-detail-label">GPU</span><span class="gauge-detail-value text-sm">${gpu.name}</span></div>
      <div class="gauge-detail-row"><span class="gauge-detail-label">VRAM</span><span class="gauge-detail-value">${gpu.vram_used_gb}/${gpu.vram_total_gb} GB (${vramPct}%)</span></div>
      <div class="gauge-detail-row"><span class="gauge-detail-label">Usage</span><span class="gauge-detail-value">${Math.round(gpu.util_percent)}%</span></div>
      <div class="gauge-detail-row"><span class="gauge-detail-label">Temp</span><span class="gauge-detail-value">${gpu.temp_c}°C</span></div>
      <div class="progress-bar" style="margin-top:8px;"><div class="progress-fill" style="width:${vramPct}%"></div></div>`;
  }

  function updateDisk(disks) {
    const content = Utils.el('disk-content');
    if (!content || !disks) return;
    content.innerHTML = disks.slice(0, 4).map(d => `
      <div style="margin-bottom:12px;">
        <div class="flex items-center justify-between text-xs" style="margin-bottom:4px;">
          <span class="gauge-detail-label text-mono">${d.path}</span>
          <span class="gauge-detail-value">${d.used_gb}/${d.total_gb} GB · ${d.percent}%</span>
        </div>
        <div class="progress-bar"><div class="progress-fill ${d.percent > 90 ? 'danger' : ''}" style="width:${d.percent}%; ${d.percent > 90 ? 'background:var(--danger)' : ''}"></div></div>
      </div>`).join('');
  }

  function updateStats(data) {
    // Fetch processes when monitor is active
    if (document.getElementById('view-monitor')?.classList.contains('active')) {
      API.system.snapshot().then(s => {
        if (s.processes) renderProcs(s.processes);
      }).catch(() => {});
    }
  }

  // ── PROCESS TABLE ────────────────────────────────────────────
  function renderProcs(procs) {
    allProcs = procs;
    displayProcs();
  }

  function displayProcs() {
    const q = (Utils.el('proc-search')?.value || '').toLowerCase();
    let filtered = allProcs.filter(p => !q || p.name.toLowerCase().includes(q));
    filtered.sort((a, b) => sortDir * ((a[sortKey] || 0) - (b[sortKey] || 0)));

    Utils.el('proc-tbody').innerHTML = filtered.map(p => `
      <tr>
        <td>${p.pid}</td>
        <td class="process-name">${p.name}</td>
        <td>${(p.cpu_percent || 0).toFixed(1)}</td>
        <td>${p.ram_mb || 0}</td>
        <td>${p.status || '—'}</td>
        <td><button class="btn btn-sm btn-ghost process-kill-btn" style="color:var(--danger);"
          onclick="if(confirm('Kill ${p.name} (PID ${p.pid})?')) Monitor.killProc(${p.pid})">Kill</button></td>
      </tr>`).join('');
  }

  function sortProcs(key) {
    if (sortKey === key) sortDir *= -1;
    else { sortKey = key; sortDir = -1; }
    displayProcs();
  }

  function filterProcs() { displayProcs(); }

  async function killProc(pid) {
    try {
      await API.post('/api/control/kill', { pid });
      Utils.toast(`Process ${pid} terminated`, 'success');
    } catch (e) {
      Utils.toast('Could not kill process: ' + e.message, 'error');
    }
  }

  return { init, sortProcs, filterProcs, killProc };
})();

window.Monitor = Monitor;
