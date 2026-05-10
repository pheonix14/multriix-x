/**
 * NeuralDesk — files.js
 * File browser and editor with atomic save, dirty tracking
 */

const Files = (() => {
  let currentPath = null;
  let currentDir = null;
  let isDirty = false;

  // Quick access paths
  const HOME = '~';

  function init() {
    browse(HOME);
    setupResizer();
    setupKeyboard();
  }

  async function browse(path) {
    currentDir = path;
    try {
      const data = await API.files.browse(path);
      if (data.error) { Utils.toast(data.error, 'error'); return; }
      renderBreadcrumb(data.path, data.parent);
      renderFileList(data.items || []);
    } catch (e) {
      Utils.toast('Could not open folder: ' + e.message, 'error');
    }
  }

  function renderBreadcrumb(fullPath, parent) {
    const parts = fullPath.replace(/\\/g, '/').split('/').filter(Boolean);
    let built = '';
    const html = parts.map((p, i) => {
      built += (i === 0 ? (fullPath.startsWith('/') ? '/' : '') : '/') + p;
      const snapshot = built.replace(/\\/g, '\\\\');
      return `<span class="breadcrumb-part" onclick="Files.browse('${snapshot}')">${p}</span>
              ${i < parts.length - 1 ? '<span class="breadcrumb-sep">/</span>' : ''}`;
    }).join('');
    Utils.el('file-breadcrumb').innerHTML = `
      <span class="breadcrumb-part" onclick="Files.browse('~')">[/]</span>
      <span class="breadcrumb-sep">/</span>${html}`;
  }

  function renderFileList(items) {
    if (!items.length) {
      Utils.el('file-list').innerHTML = `<div style="padding:var(--sp-5); text-align:center; color:var(--text-tertiary); font-size:var(--text-sm);">Empty folder</div>`;
      return;
    }

    const icons = {
      '.py': '[py]', '.js': '[js]', '.json': '[{}]', '.md': '[md]',
      '.txt': '[T]', '.sh': '[>_]', '.yaml': '[y]', '.yml': '[y]',
      '.css': '[css]', '.html': '[<>]',
    };
    const getIcon = (item) => {
      if (item.type === 'folder') return '[+]';
      if (item.is_modelfile) return '[M]';
      return icons[item.extension] || '[-]';
    };

    Utils.el('file-list').innerHTML = items.map(item => `
      <div class="file-item${item.is_modelfile ? ' is-modelfile' : ''}${item.path === currentPath ? ' active' : ''}"
           onclick="${item.type === 'folder' ? `Files.browse('${item.path.replace(/\\/g, '\\\\')}')` : `Files.openFile('${item.path.replace(/\\/g, '\\\\')}')`}"
           title="${item.path}">
        <span class="fi-icon">${getIcon(item)}</span>
        <span class="fi-name">${item.name}</span>
        ${item.type === 'file' ? `<span class="fi-size">${Utils.formatBytes(item.size_bytes)}</span>` : ''}
      </div>`
    ).join('');
  }

  async function openFile(path) {
    if (isDirty && currentPath) {
      if (!confirm('You have unsaved changes. Discard and open new file?')) return;
    }

    currentPath = path;
    isDirty = false;

    Utils.el('editor-filepath').textContent = path;
    Utils.el('editor-dirty-dot').style.display = 'none';
    Utils.el('editor-save-btn').disabled = false;
    Utils.hide('editor-empty');
    Utils.show('file-editor-textarea');

    const ta = Utils.el('file-editor-textarea');
    ta.value = 'Loading…';
    ta.disabled = true;

    try {
      const data = await API.files.read(path);
      if (data.error) { Utils.toast(data.error, 'error'); return; }
      ta.value = data.content;
      ta.disabled = false;
      ta.focus();
    } catch (e) {
      Utils.toast('Could not read file: ' + e.message, 'error');
    }
  }

  async function save() {
    if (!currentPath) return;
    const content = Utils.el('file-editor-textarea').value;
    try {
      const result = await API.files.write(currentPath, content);
      if (result.success) {
        isDirty = false;
        Utils.el('editor-dirty-dot').style.display = 'none';
        Utils.toast('File saved!', 'success');
      } else {
        Utils.toast('Save failed: ' + (result.error || 'Unknown error'), 'error');
      }
    } catch (e) {
      Utils.toast('Save failed: ' + e.message, 'error');
    }
  }

  function markDirty() {
    if (!isDirty) {
      isDirty = true;
      Utils.el('editor-dirty-dot').style.display = 'block';
    }
  }

  function copyAll() {
    const ta = Utils.el('file-editor-textarea');
    if (ta && ta.value) Utils.copyText(ta.value);
  }

  function goUp() {
    if (!currentDir) return;
    const parent = currentDir.replace(/[\\/][^\\/]+$/, '') || '/';
    browse(parent || '~');
  }

  function refresh() {
    if (currentDir) browse(currentDir);
  }

  function search() {
    const q = Utils.el('file-search').value.toLowerCase();
    const items = Utils.el('file-list').querySelectorAll('.file-item');
    items.forEach(item => {
      const name = item.querySelector('.fi-name')?.textContent.toLowerCase() || '';
      item.style.display = name.includes(q) ? '' : 'none';
    });
  }

  // ── RESIZER ──────────────────────────────────────────────────
  function setupResizer() {
    const resizer = Utils.el('files-resizer');
    if (!resizer) return;
    let dragging = false;
    let startX = 0;
    let startW = 0;

    resizer.addEventListener('mousedown', e => {
      dragging = true;
      startX = e.clientX;
      startW = Utils.el('view-files').querySelector('.files-browser').offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });
    document.addEventListener('mousemove', e => {
      if (!dragging) return;
      const browser = Utils.el('view-files').querySelector('.files-browser');
      const newW = Math.max(180, Math.min(600, startW + (e.clientX - startX)));
      browser.style.width = newW + 'px';
    });
    document.addEventListener('mouseup', () => {
      dragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    });
  }

  // ── NEW FILE CREATION ───────────────────────────────────────
  async function newFile() {
    const name = prompt("Enter new file name (with extension, e.g. script.py, index.html):");
    if (!name) return;
    const path = (currentDir && currentDir !== '~') ? `${currentDir}/${name}` : `~/${name}`;
    try {
      const res = await API.files.write(path, "");
      if (res.success) {
        Utils.toast("File created successfully!", "success");
        await browse(currentDir || '~');
        openFile(path);
      } else {
        Utils.toast("Creation failed: " + (res.error || "Unknown error"), "error");
      }
    } catch (e) {
      Utils.toast("Creation failed: " + e.message, "error");
    }
  }

  // ── CODE BLOCK INTEGRATION ───────────────────────────────────
  async function loadCodeSnippet(code, filename = 'snippet.py') {
    // Switch to files view first
    if (window.App && typeof App.switchView === 'function') {
      App.switchView('files');
    }
    
    // Prompt to choose custom filename
    const name = prompt("Save code block to Editor Workspace as filename:", filename);
    if (!name) return;
    
    // Default workspace is currentDir or HOME
    const targetDir = currentDir || HOME;
    const path = targetDir !== '~' ? `${targetDir}/${name}` : `~/${name}`;
    
    try {
      const res = await API.files.write(path, code);
      if (res.success) {
        Utils.toast(`Loaded into Editor: ${name}`, "success");
        await browse(targetDir);
        openFile(path);
      } else {
        Utils.toast("Error saving code block: " + (res.error || "Unknown"), "error");
      }
    } catch (e) {
      Utils.toast("Error loading snippet: " + e.message, "error");
    }
  }

  // ── KEYBOARD SHORTCUTS ───────────────────────────────────────
  function setupKeyboard() {
    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (currentPath) save();
      }
    });
  }

  return { init, browse, openFile, save, markDirty, copyAll, goUp, refresh, search, newFile, loadCodeSnippet };
})();

window.Files = Files;
