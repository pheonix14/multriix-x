const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const cpuStat = document.getElementById('cpu-stat');
const ramStat = document.getElementById('ram-stat');
const gpuStat = document.getElementById('gpu-stat');
const aiStatus = document.getElementById('ai-status');

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;

const chatWs = new WebSocket(`${protocol}//${host}/ws/chat`);
const statsWs = new WebSocket(`${protocol}//${host}/ws/stats`);

chatWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (!data.done) {
        appendToken(data.token, data.active_model);
        aiStatus.innerText = `GENERATING [${data.active_model}]...`;
    } else {
        aiStatus.innerText = `IDLE [TPS: ${data.stats.tps.toFixed(1)}]`;
    }
};

statsWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    cpuStat.innerText = `${data.cpu_percent}%`;
    ramStat.innerText = `${(data.ram.used / 1024 / 1024 / 1024).toFixed(1)}GB`;
    if (data.gpu && data.gpu.length > 0) {
        gpuStat.innerText = `${data.gpu[0].load.toFixed(0)}%`;
    }
    updateDetailedStats(data);
};

function appendToken(token, model) {
    let lastMsg = chatHistory.lastElementChild;
    if (!lastMsg || lastMsg.classList.contains('user')) {
        lastMsg = document.createElement('div');
        lastMsg.className = 'message ai';
        chatHistory.appendChild(lastMsg);
    }
    lastMsg.innerText += token;
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function sendMessage() {
    const msg = chatInput.value;
    if (!msg) return;
    
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.innerText = msg;
    chatHistory.appendChild(userMsg);
    
    chatWs.send(JSON.stringify({
        message: msg,
        models: {
            "qwen2.5:7b": document.getElementById('mix-qwen').value / 100,
            "mistral:7b": document.getElementById('mix-mistral').value / 100
        }
    }));
    
    chatInput.value = '';
    aiStatus.innerText = 'THINKING...';
}

sendBtn.onclick = sendMessage;
chatInput.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };

function updateDetailedStats(data) {
    const container = document.getElementById('detailed-stats');
    container.innerHTML = `
        <div class="stat-row"><span>CPU CORES</span> <span>${data.cpu_cores}</span></div>
        <div class="progress-bar"><div class="progress-fill" style="width: ${data.cpu_percent}%"></div></div>
        
        <div class="stat-row" style="margin-top:10px;"><span>RAM USAGE</span> <span>${data.ram.percent}%</span></div>
        <div class="progress-bar"><div class="progress-fill" style="width: ${data.ram.percent}%"></div></div>
    `;
}
