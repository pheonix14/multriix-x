document.addEventListener('DOMContentLoaded', async () => {
    const configEditor = document.getElementById('config-editor');
    const saveBtn = document.getElementById('save-config-btn');
    if (!configEditor) return;

    let currentConfig = {};

    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            currentConfig = await res.json();
            renderConfig();
        } catch (e) {
            console.error("Failed to load config", e);
        }
    }

    function renderConfig() {
        configEditor.innerHTML = '';
        for (const [section, keys] of Object.entries(currentConfig)) {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'config-section';
            
            const title = document.createElement('h3');
            title.innerText = `[${section}]`;
            title.style.color = 'var(--neon-cyan)';
            sectionDiv.appendChild(title);

            for (const [key, value] of Object.entries(keys)) {
                const row = document.createElement('div');
                row.className = 'config-row';
                row.style.display = 'flex';
                row.style.marginBottom = '10px';
                
                const label = document.createElement('label');
                label.innerText = key;
                label.style.width = '200px';
                label.style.color = '#fff';

                let input;
                if (typeof value === 'boolean') {
                    input = document.createElement('input');
                    input.type = 'checkbox';
                    input.checked = value;
                } else if (typeof value === 'number') {
                    input = document.createElement('input');
                    input.type = 'number';
                    input.value = value;
                } else {
                    input = document.createElement('input');
                    input.type = 'text';
                    input.value = value;
                }

                input.dataset.section = section;
                input.dataset.key = key;
                input.style.flex = '1';
                input.style.background = 'transparent';
                input.style.border = '1px solid var(--neon-cyan)';
                input.style.color = '#0ff';
                input.style.padding = '5px';

                row.appendChild(label);
                row.appendChild(input);
                sectionDiv.appendChild(row);
            }
            configEditor.appendChild(sectionDiv);
        }
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const inputs = configEditor.querySelectorAll('input');
            const updates = {};

            inputs.forEach(input => {
                const sec = input.dataset.section;
                const key = input.dataset.key;
                let val = input.value;

                if (input.type === 'checkbox') val = input.checked;
                else if (input.type === 'number') val = Number(val);

                if (!updates[sec]) updates[sec] = {};
                updates[sec][key] = val;
            });

            try {
                await fetch('/api/config/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updates)
                });
                alert('Config saved dynamically!');
            } catch (e) {
                alert('Failed to save config');
            }
        });
    }

    loadConfig();
});
