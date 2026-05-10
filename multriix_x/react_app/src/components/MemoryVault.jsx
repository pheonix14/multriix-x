import React, { useState, useEffect } from 'react';

export default function MemoryVault() {
    const [memory, setMemory] = useState({ short_term: [], long_term: [] });
    const [newFact, setNewFact] = useState('');

    useEffect(() => {
        loadMemory();
    }, []);

    const loadMemory = async () => {
        try {
            const res = await fetch('/api/memory?session_id=default');
            const data = await res.json();
            setMemory(data);
        } catch (e) {
            console.error("Failed to load memory", e);
        }
    };

    const injectMemory = async () => {
        if (!newFact.trim()) return;
        try {
            await fetch('/api/memory/inject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact: newFact, tags: ['user_injected'] })
            });
            setNewFact('');
            loadMemory();
        } catch (e) {
            console.error("Failed to inject memory", e);
        }
    };

    const deleteMemory = async (id) => {
        try {
            await fetch(`/api/memory/${id}`, { method: 'DELETE' });
            loadMemory();
        } catch (e) {
            console.error("Failed to delete memory", e);
        }
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #0ff', background: 'rgba(0,10,10,0.8)', color: '#0ff' }}>
            <h3 style={{ margin: '0 0 15px 0' }}>MEMORY VAULT</h3>
            
            <div style={{ display: 'flex', marginBottom: '20px' }}>
                <input 
                    value={newFact}
                    onChange={(e) => setNewFact(e.target.value)}
                    placeholder="Inject fact directly into AI core..."
                    style={{ flex: 1, background: 'rgba(0,20,20,0.5)', border: '1px solid #0ff', color: '#0ff', padding: '10px' }}
                />
                <button 
                    onClick={injectMemory}
                    style={{ background: 'transparent', border: '1px solid #0ff', color: '#0ff', padding: '0 20px', marginLeft: '10px', cursor: 'pointer' }}
                >
                    INJECT
                </button>
            </div>

            <div style={{ height: '300px', overflowY: 'auto' }}>
                <h4 style={{ borderBottom: '1px solid #0ff', paddingBottom: '5px' }}>LONG-TERM STORAGE</h4>
                {memory.long_term.map(m => (
                    <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', borderBottom: '1px dotted rgba(0,255,255,0.3)' }}>
                        <div>
                            <div>{m.content}</div>
                            <div style={{ fontSize: '0.8em', color: 'rgba(0,255,255,0.5)' }}>Tags: {m.tags?.join(', ')}</div>
                        </div>
                        <button onClick={() => deleteMemory(m.id)} style={{ background: 'transparent', border: 'none', color: '#f00', cursor: 'pointer' }}>[X]</button>
                    </div>
                ))}
            </div>
        </div>
    );
}
