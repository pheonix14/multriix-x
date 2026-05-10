import React, { useState, useEffect } from 'react';

export default function ModelMixer() {
    const [config, setConfig] = useState({ enabled: false, mode: 'sequential', ratios: { qwen: 0.5, mistral: 0.5 } });

    useEffect(() => {
        fetch('/api/mixer/config')
            .then(res => res.json())
            .then(data => setConfig(data))
            .catch(console.error);
    }, []);

    const updateConfig = async (newConf) => {
        const updated = { ...config, ...newConf };
        setConfig(updated);
        try {
            await fetch('/api/mixer/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updated)
            });
        } catch (e) {
            console.error(e);
        }
    };

    const handleRatioChange = (model, val) => {
        const num = parseFloat(val);
        const newRatios = { ...config.ratios, [model]: num };
        
        // Normalize if sum > 1
        const sum = Object.values(newRatios).reduce((a,b)=>a+b, 0);
        if (sum > 1 && num > config.ratios[model]) {
            const diff = sum - 1;
            const otherModel = Object.keys(newRatios).find(k => k !== model);
            if (otherModel) {
                newRatios[otherModel] = Math.max(0, newRatios[otherModel] - diff);
            }
        }
        updateConfig({ ratios: newRatios });
    };

    return (
        <div style={{ padding: '20px', border: '1px solid #0ff', background: 'rgba(0,10,10,0.8)', color: '#0ff' }}>
            <h3 style={{ margin: '0 0 15px 0' }}>MODEL MIXER (ENSEMBLE)</h3>
            
            <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                    <input 
                        type="checkbox" 
                        checked={config.enabled} 
                        onChange={(e) => updateConfig({ enabled: e.target.checked })} 
                        style={{ marginRight: '10px' }}
                    />
                    ENABLE MODEL MIXING
                </label>
            </div>

            {config.enabled && (
                <>
                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', marginBottom: '5px' }}>Mixing Mode:</label>
                        <select 
                            value={config.mode}
                            onChange={(e) => updateConfig({ mode: e.target.value })}
                            style={{ width: '100%', background: '#000', color: '#0ff', border: '1px solid #0ff', padding: '5px' }}
                        >
                            <option value="sequential">Sequential (Pass outputs)</option>
                            <option value="parallel">Parallel (Merge outputs)</option>
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', marginBottom: '5px' }}>Influence Ratios:</label>
                        {Object.entries(config.ratios).map(([model, ratio]) => (
                            <div key={model} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
                                <span style={{ width: '80px', textTransform: 'uppercase' }}>{model}</span>
                                <input 
                                    type="range" 
                                    min="0" max="1" step="0.05"
                                    value={ratio}
                                    onChange={(e) => handleRatioChange(model, e.target.value)}
                                    style={{ flex: 1, margin: '0 10px' }}
                                />
                                <span>{(ratio * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
