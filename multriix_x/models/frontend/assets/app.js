document.addEventListener('DOMContentLoaded', () => {
    // ── NAVIGATION ──
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            const targetId = item.getAttribute('data-target');
            views.forEach(view => {
                view.classList.remove('active');
                if (view.id === targetId) {
                    view.classList.add('active');
                }
            });
        });
    });

    // ── MODEL SELECTOR ──
    const modelDropdown = document.getElementById('model-dropdown');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');

    async function loadModels() {
        try {
            const res = await fetch('/api/models');
            const data = await res.json();
            
            modelDropdown.innerHTML = '';
            
            let allModels = [];
            if (data.ollama && data.ollama.length > 0) {
                data.ollama.forEach(m => allModels.push({ id: m, name: `Ollama: ${m}` }));
            }
            if (data.local_hf && data.local_hf.length > 0) {
                data.local_hf.forEach(m => allModels.push({ id: m, name: `Local: ${m}` }));
            }
            if (data.standalone && data.standalone.length > 0) {
                data.standalone.forEach(m => allModels.push({ id: m, name: `Fallback: ${m}` }));
            }

            if (allModels.length === 0) {
                modelDropdown.innerHTML = '<option>No models found</option>';
                statusText.innerText = 'No models installed';
                statusDot.style.backgroundColor = '#ff3b30'; // red
            } else {
                allModels.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.innerText = m.name;
                    modelDropdown.appendChild(opt);
                });
                statusText.innerText = 'Ready';
                statusDot.style.backgroundColor = '#34c759'; // green
            }
        } catch (e) {
            console.error(e);
            modelDropdown.innerHTML = '<option>API Offline</option>';
            statusText.innerText = 'Server offline';
            statusDot.style.backgroundColor = '#ff3b30';
        }
    }
    loadModels();

    // ── CHAT ──
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    
    let ws = null;
    let currentAssistantMessage = null;

    function connectWS() {
        ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.error) {
                if (!currentAssistantMessage) {
                    currentAssistantMessage = document.createElement('div');
                    currentAssistantMessage.className = 'message ai';
                    currentAssistantMessage.style.color = '#ff3b30';
                    chatMessages.appendChild(currentAssistantMessage);
                }
                currentAssistantMessage.innerText += "\n[Error]: " + data.error;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else if (data.token) {
                if (!currentAssistantMessage) {
                    currentAssistantMessage = document.createElement('div');
                    currentAssistantMessage.className = 'message ai';
                    chatMessages.appendChild(currentAssistantMessage);
                }
                // Handle newlines simply
                const textNode = document.createTextNode(data.token);
                currentAssistantMessage.appendChild(textNode);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            if (data.done) {
                currentAssistantMessage = null;
            }
        };
        ws.onclose = () => setTimeout(connectWS, 2000);
    }
    connectWS();

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;
        
        // Add User message
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.innerText = text;
        chatMessages.appendChild(userMsg);
        
        // Send to backend
        const selectedModel = modelDropdown.value;
        const temp = parseFloat(document.getElementById('cfg-temperature').value);
        const maxTok = parseInt(document.getElementById('cfg-max-tokens').value);

        ws.send(JSON.stringify({
            message: text,
            model: selectedModel,
            temperature: temp,
            max_tokens: maxTok
        }));
        
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // ── SETTINGS (Visual Editor) ──
    const tempSlider = document.getElementById('cfg-temperature');
    const tempVal = document.getElementById('cfg-temperature-val');
    tempSlider.addEventListener('input', () => {
        tempVal.innerText = tempSlider.value;
    });

    async function loadSettings() {
        try {
            const res = await fetch('/api/config');
            const cfg = await res.json();
            if (cfg.BRAIN) {
                tempSlider.value = cfg.BRAIN.temperature || 0.7;
                tempVal.innerText = tempSlider.value;
                document.getElementById('cfg-max-tokens').value = cfg.BRAIN.max_tokens || 4096;
            }
            if (cfg.SYSTEM) {
                document.getElementById('cfg-system-prompt').value = cfg.SYSTEM.system_prompt || '';
            }
            if (cfg.MEMORY) {
                document.getElementById('cfg-long-term').checked = cfg.MEMORY.long_term_enabled;
            }
        } catch (e) { console.error("Config fetch failed", e); }
    }
    loadSettings();

    document.getElementById('save-settings-btn').addEventListener('click', async () => {
        const updates = {
            "BRAIN": {
                "temperature": parseFloat(tempSlider.value),
                "max_tokens": parseInt(document.getElementById('cfg-max-tokens').value)
            },
            "SYSTEM": {
                "system_prompt": document.getElementById('cfg-system-prompt').value
            },
            "MEMORY": {
                "long_term_enabled": document.getElementById('cfg-long-term').checked
            }
        };
        try {
            await fetch('/api/config/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(updates)
            });
            alert("Settings saved successfully!");
        } catch (e) {
            alert("Failed to save settings.");
        }
    });

    // ── FILE EDITOR ──
    const editorSelect = document.getElementById('editor-file-select');
    const editorTextarea = document.getElementById('editor-textarea');

    async function loadFileEditor() {
        const fileToLoad = editorSelect.value; // 'config.json' or 'modelfile'
        const fullPath = fileToLoad === 'config.json' ? 'config.json' : 'Modelfile';
        
        try {
            const res = await fetch('/api/control/read', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ path: fullPath })
            });
            const data = await res.json();
            if (data.content !== undefined) {
                editorTextarea.value = data.content;
            } else {
                editorTextarea.value = "File not found. You can create it by saving.";
            }
        } catch (e) {
            editorTextarea.value = "Error loading file.";
        }
    }

    editorSelect.addEventListener('change', loadFileEditor);
    // Initial load
    loadFileEditor();

    document.getElementById('editor-save-btn').addEventListener('click', async () => {
        const fileToLoad = editorSelect.value;
        const fullPath = fileToLoad === 'config.json' ? 'config.json' : 'Modelfile';
        const content = editorTextarea.value;

        try {
            await fetch('/api/control/write', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ path: fullPath, content: content })
            });
            alert("File saved directly!");
        } catch (e) {
            alert("Failed to save file.");
        }
    });

    document.getElementById('editor-explain-btn').addEventListener('click', () => {
        alert("This file controls raw parameters. 'config.json' holds your app settings. 'Modelfile' holds Ollama model creation recipes.");
    });
});
