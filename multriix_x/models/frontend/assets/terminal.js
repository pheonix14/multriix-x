class Terminal {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.history = [];
        this.historyIndex = 0;
        this.setupUI();
    }

    setupUI() {
        this.outputArea = document.createElement('div');
        this.outputArea.className = 'terminal-output';
        this.outputArea.style.height = '400px';
        this.outputArea.style.overflowY = 'auto';
        this.outputArea.style.fontFamily = 'monospace';
        this.outputArea.style.color = '#0ff';
        this.outputArea.style.padding = '10px';
        this.outputArea.style.background = '#000';
        this.outputArea.style.border = '1px solid #0ff';
        this.outputArea.style.marginBottom = '10px';

        this.inputArea = document.createElement('div');
        this.inputArea.style.display = 'flex';
        this.inputArea.style.alignItems = 'center';

        this.prompt = document.createElement('span');
        this.prompt.innerText = 'MULTRIIX> ';
        this.prompt.style.color = '#0ff';
        this.prompt.style.fontFamily = 'monospace';
        this.prompt.style.marginRight = '10px';

        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.style.flex = '1';
        this.input.style.background = 'transparent';
        this.input.style.border = 'none';
        this.input.style.color = '#0ff';
        this.input.style.fontFamily = 'monospace';
        this.input.style.outline = 'none';
        
        this.inputArea.appendChild(this.prompt);
        this.inputArea.appendChild(this.input);

        this.container.appendChild(this.outputArea);
        this.container.appendChild(this.inputArea);

        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
    }

    print(text, isError=false) {
        const line = document.createElement('div');
        line.innerText = text;
        line.style.color = isError ? '#f00' : '#0ff';
        line.style.whiteSpace = 'pre-wrap';
        this.outputArea.appendChild(line);
        this.outputArea.scrollTop = this.outputArea.scrollHeight;
    }

    async executeCommand(cmd) {
        if (!cmd.trim()) return;
        
        this.print(`MULTRIIX> ${cmd}`);
        this.history.push(cmd);
        this.historyIndex = this.history.length;
        
        this.input.value = '';
        
        if (cmd.trim() === 'clear') {
            this.outputArea.innerHTML = '';
            return;
        }

        try {
            const res = await fetch('/api/control/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            });
            const data = await res.json();
            
            if (data.stdout) this.print(data.stdout);
            if (data.stderr) this.print(data.stderr, true);
            if (data.error) this.print(data.error, true);
            
        } catch (err) {
            this.print(`Execution failed: ${err.message}`, true);
        }
    }

    handleKeydown(e) {
        if (e.key === 'Enter') {
            this.executeCommand(this.input.value);
        } else if (e.key === 'ArrowUp') {
            if (this.historyIndex > 0) {
                this.historyIndex--;
                this.input.value = this.history[this.historyIndex];
            }
            e.preventDefault();
        } else if (e.key === 'ArrowDown') {
            if (this.historyIndex < this.history.length - 1) {
                this.historyIndex++;
                this.input.value = this.history[this.historyIndex];
            } else {
                this.historyIndex = this.history.length;
                this.input.value = '';
            }
            e.preventDefault();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('terminal-container')) {
        window.multriixTerminal = new Terminal('terminal-container');
    }
});
