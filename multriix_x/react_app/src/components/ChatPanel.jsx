import React, { useState, useEffect, useRef } from 'react';

export default function ChatPanel() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const wsRef = useRef(null);

    useEffect(() => {
        connectWS();
        return () => wsRef.current?.close();
    }, []);

    const connectWS = () => {
        const ws = new WebSocket(`ws://${window.location.host}/ws/chat`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.token) {
                setMessages(prev => {
                    const newMsgs = [...prev];
                    if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'assistant') {
                        newMsgs[newMsgs.length - 1].content += data.token;
                    } else {
                        newMsgs.push({ role: 'assistant', content: data.token });
                    }
                    return newMsgs;
                });
            }
        };

        ws.onclose = () => {
            setTimeout(connectWS, 2000);
        };
    };

    const sendMessage = () => {
        if (!input.trim() || !wsRef.current) return;
        
        setMessages(prev => [...prev, { role: 'user', content: input }]);
        wsRef.current.send(JSON.stringify({
            message: input,
            session_id: 'default',
            mix: false
        }));
        setInput('');
    };

    return (
        <div className="chat-panel">
            <div className="messages" style={{ height: '400px', overflowY: 'auto', padding: '10px' }}>
                {messages.map((m, i) => (
                    <div key={i} style={{ marginBottom: 10, color: m.role === 'user' ? '#fff' : '#0ff' }}>
                        <strong>{m.role === 'user' ? 'USER: ' : 'MULTRIIX: '}</strong>
                        <span style={{ whiteSpace: 'pre-wrap' }}>{m.content}</span>
                    </div>
                ))}
            </div>
            <div style={{ display: 'flex', borderTop: '1px solid #0ff', padding: '10px' }}>
                <input 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    style={{ flex: 1, background: 'transparent', border: 'none', color: '#0ff', outline: 'none' }}
                    placeholder="Enter command..."
                />
            </div>
        </div>
    );
}
