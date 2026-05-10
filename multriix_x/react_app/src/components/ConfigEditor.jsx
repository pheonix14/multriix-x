import React, { useState, useEffect } from 'react';

export default function ConfigEditor() {
    const [config, setConfig] = useState({});

    useEffect(() => {
        fetch('/api/config')
            .then(res => res.json())
            .then(data => setConfig(data))
            .catch(err => console.error("Config fetch error", err));
    }, []);

    const handleChange = (section, key, value) => {
        setConfig(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value
            }
        }));
    };

    const handleSave = async () => {
        try {
            await fetch('/api/config/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            alert("Config updated live!");
        } catch (e) {
            alert("Failed to update config");
        }
    };

    return (
        <div style={{ padding: '20px', color: '#0ff' }}>
            <h2 style={{ textShadow: '0 0 10px #0ff' }}>LIVE CONFIG EDITOR</h2>
            <div style={{ height: '400px', overflowY: 'auto' }}>
                {Object.entries(config).map(([section, keys]) => (
                    <div key={section} style={{ marginBottom: '20px' }}>
                        <h3 style={{ borderBottom: '1px solid #0ff', paddingBottom: '5px' }}>[{section}]</h3>
                        {Object.entries(keys).map(([key, value]) => (
                            <div key={key} style={{ display: 'flex', marginBottom: '5px' }}>
                                <label style={{ width: '200px' }}>{key}</label>
                                {typeof value === 'boolean' ? (
                                    <input 
                                        type="checkbox" 
                                        checked={value}
                                        onChange={(e) => handleChange(section, key, e.target.checked)}
                                    />
                                ) : (
                                    <input 
                                        type={typeof value === 'number' ? 'number' : 'text'}
                                        value={value}
                                        onChange={(e) => handleChange(section, key, 
                                            e.target.type === 'number' ? Number(e.target.value) : e.target.value)}
                                        style={{ flex: 1, background: 'rgba(0,20,20,0.5)', border: '1px solid #0ff', color: '#0ff', padding: '5px' }}
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
            <button 
                onClick={handleSave}
                style={{ 
                    marginTop: '20px', padding: '10px 20px', 
                    background: 'transparent', border: '1px solid #0ff', 
                    color: '#0ff', cursor: 'pointer',
                    boxShadow: '0 0 10px inset #0ff'
                }}>
                SAVE & APPLY LIVE
            </button>
        </div>
    );
}
