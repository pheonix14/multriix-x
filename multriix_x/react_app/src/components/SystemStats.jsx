import React, { useState, useEffect } from 'react';

export default function SystemStats() {
    const [stats, setStats] = useState({
        cpu_percent: 0,
        ram: { percent: 0, used_gb: 0, total_gb: 0 },
        swap: { percent: 0 }
    });

    useEffect(() => {
        const ws = new WebSocket(`ws://${window.location.host}/ws/stats`);
        ws.onmessage = (event) => {
            setStats(JSON.parse(event.data));
        };
        return () => ws.close();
    }, []);

    const ProgressBar = ({ label, percent, detail }) => (
        <div style={{ marginBottom: '15px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>{label}</span>
                <span>{detail || `${percent.toFixed(1)}%`}</span>
            </div>
            <div style={{ height: '10px', background: 'rgba(0,255,255,0.2)', width: '100%' }}>
                <div style={{ 
                    height: '100%', 
                    width: `${percent}%`, 
                    background: percent > 80 ? '#f00' : '#0ff',
                    transition: 'width 0.5s ease-out'
                }} />
            </div>
        </div>
    );

    return (
        <div style={{ padding: '20px', border: '1px solid #0ff', background: 'rgba(0,10,10,0.8)', color: '#0ff' }}>
            <h3 style={{ margin: '0 0 15px 0' }}>SYSTEM DIAGNOSTICS</h3>
            <ProgressBar label="CPU USAGE" percent={stats.cpu_percent} />
            <ProgressBar 
                label="RAM USAGE" 
                percent={stats.ram.percent} 
                detail={`${stats.ram.used_gb.toFixed(1)} / ${stats.ram.total_gb.toFixed(1)} GB`} 
            />
            <ProgressBar label="SWAP" percent={stats.swap.percent} />
        </div>
    );
}
