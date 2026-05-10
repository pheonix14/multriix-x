import React, { useState, useRef } from 'react';

export default function PCControl() {
    const [history, setHistory] = useState([]);
    const [input, setInput] = useState('');
    const bottomRef = useRef(null);

    const executeCommand = async () => {
        if (!input.trim()) return;
        
        const cmd = input;
        setInput('');
        setHistory(prev => [...prev, { type: 'cmd', text: `MULTRIIX> ${cmd}` }]);

        if (cmd === 'clear') {
            setHistory([]);
            return;
        }

        try {
            const res = await fetch('/api/control/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            });
            const data = await res.json();
            
            if (data.stdout) setHistory(prev => [...prev, { type: 'out', text: data.stdout }]);
            if (data.stderr) setHistory(prev => [...prev, { type: 'err', text: data.stderr }]);
            if (data.error) setHistory(prev => [...prev, { type: 'err', text: data.error }]);
            
        } catch (err) {
            setHistory(prev => [...prev, { type: 'err', text: `Failed: ${err.message}` }]);
        }
        
        setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', border: '1px solid #0ff', background: '#000' }}>
            <div style={{ background: '#0ff', color: '#000', padding: '5px 10px', fontWeight: 'bold' }}>
                TERMINAL / PC CONTROL
            </div>
            <div style={{ flex: 1, padding: '10px', overflowY: 'auto', fontFamily: 'monospace' }}>
                {history.map((h, i) => (
                    <div key={i} style={{ 
                        color: h.type === 'err' ? '#f00' : '#0ff',
                        whiteSpace: 'pre-wrap',
                        marginBottom: '5px'
                    }}>
                        {h.text}
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
            <div style={{ display: 'flex', borderTop: '1px solid #0ff', padding: '10px' }}>
                <span style={{ color: '#0ff', marginRight: '10px', fontFamily: 'monospace' }}>MULTRIIX></span>
                <input 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && executeCommand()}
                    style={{ flex: 1, background: 'transparent', border: 'none', color: '#0ff', fontFamily: 'monospace', outline: 'none' }}
                    autoFocus
                />
            </div>
        </div>
    );
}
