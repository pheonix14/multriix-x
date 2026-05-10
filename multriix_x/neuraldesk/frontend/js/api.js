/**
 * NeuralDesk — api.js
 * All fetch/WebSocket API calls to the backend
 */

const API = (() => {
  const BASE = window.location.origin;
  const WS_BASE = `ws://${window.location.host}`;

  async function get(path) {
    const r = await fetch(BASE + path);
    if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
    return r.json();
  }

  async function post(path, data) {
    const r = await fetch(BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
    return r.json();
  }

  async function del(path) {
    const r = await fetch(BASE + path, { method: 'DELETE' });
    if (!r.ok) throw new Error(`DELETE ${path} → ${r.status}`);
    return r.json();
  }

  // Models
  const models = {
    list:   () => get('/api/models'),
    pull:   (name) => post('/api/models/pull', { name }),
    delete: (name) => del(`/api/models/${encodeURIComponent(name)}`),
    info:   (name) => get(`/api/models/${encodeURIComponent(name)}/info`),
  };

  // Config
  const config = {
    get:    () => get('/api/config'),
    save:   (data) => post('/api/config', data),
    reset:  () => post('/api/config/reset', {}),
  };

  // Files
  const files = {
    browse: (path) => get(`/api/files/browse?path=${encodeURIComponent(path)}`),
    read:   (path) => post('/api/files/read', { path }),
    write:  (path, content) => post('/api/files/write', { path, content }),
  };

  // Sessions
  const sessions = {
    list:   () => get('/api/sessions'),
    get:    (id) => get(`/api/sessions/${id}`),
    delete: (id) => del(`/api/sessions/${id}`),
  };

  // System
  const system = {
    snapshot: () => get('/api/system'),
    processes: () => get('/api/system/processes'),
  };

  // WebSocket factory
  function ws(path, onMessage, onError) {
    let socket = null;
    let reconnectTimer = null;

    function connect() {
      socket = new WebSocket(WS_BASE + path);
      socket.onmessage = (e) => onMessage(JSON.parse(e.data));
      socket.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000);
      };
      socket.onerror = (e) => {
        if (onError) onError(e);
      };
    }

    connect();

    return {
      send: (data) => socket?.readyState === WebSocket.OPEN && socket.send(JSON.stringify(data)),
      close: () => { clearTimeout(reconnectTimer); socket?.close(); },
      isOpen: () => socket?.readyState === WebSocket.OPEN,
    };
  }

  return { get, post, del, models, config, files, sessions, system, ws };
})();

window.API = API;
