import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

export default function LiveBrain() {
    const mountRef = useRef(null);
    const [stats, setStats] = useState({ tps: 0, tokens: 0, status: 'WAITING', stream: '' });

    useEffect(() => {
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000505, 0.03);

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        
        renderer.setSize(window.innerWidth, window.innerHeight);
        mountRef.current.appendChild(renderer.domElement);

        const networkGroup = new THREE.Group();
        const particleGroup = new THREE.Group();
        scene.add(networkGroup);
        scene.add(particleGroup);
        camera.position.set(0, 20, 70);

        // Materials
        const nodeMatInactive = new THREE.MeshBasicMaterial({ color: 0x008888, transparent: true, opacity: 0.5 });
        const nodeMatActive = new THREE.MeshBasicMaterial({ color: 0xffffff });
        const nodeMatAttn = new THREE.MeshBasicMaterial({ color: 0xff8800 });
        const lineMat = new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.8 });

        const layerZ = { "embedding": -30, "attention_1": -10, "ffn_1": 10, "output": 30 };
        const nodeMeshes = {};

        // Particles
        const partGeo = new THREE.BufferGeometry();
        const partPos = new Float32Array(3000);
        for(let i=0; i<3000; i++) partPos[i] = (Math.random()-0.5)*100;
        partGeo.setAttribute('position', new THREE.BufferAttribute(partPos, 3));
        const partMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.3, blending: THREE.AdditiveBlending });
        const particles = new THREE.Points(partGeo, partMat);
        particleGroup.add(particles);

        let ws = new WebSocket(`ws://${window.location.host}/ws/brain`);
        let isThinking = false;
        let rotAngle = 0;

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            isThinking = data.thinking;
            
            setStats({
                tps: data.tokens_per_second || 0,
                tokens: data.token_stream ? data.token_stream.length : 0,
                status: isThinking ? 'THINKING...' : 'IDLE',
                stream: data.token_stream ? data.token_stream.join(' ') : ''
            });
            
            // Nodes
            if (data.nodes) {
                data.nodes.forEach(n => {
                    if (!nodeMeshes[n.id]) {
                        const m = new THREE.Mesh(new THREE.SphereGeometry(1.2, 8, 8), nodeMatInactive);
                        m.position.set(n.x/10 - 10, n.y/10, layerZ[n.layer] || 0);
                        networkGroup.add(m);
                        nodeMeshes[n.id] = m;
                    }
                    const mesh = nodeMeshes[n.id];
                    if (n.activation > 0.8) mesh.material = nodeMatAttn;
                    else if (n.activation > 0.4) mesh.material = nodeMatActive;
                    else mesh.material = nodeMatInactive;
                    const sc = 1 + n.activation;
                    mesh.scale.set(sc, sc, sc);
                });
            }

            // Zap connections
            if (isThinking && data.connections) {
                data.connections.filter(c => c.active).slice(0,30).forEach(c => {
                    const p1 = nodeMeshes[c.from]?.position;
                    const p2 = nodeMeshes[c.to]?.position;
                    if(p1 && p2) {
                        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([p1, p2]), lineMat);
                        networkGroup.add(line);
                        setTimeout(() => networkGroup.remove(line), 100);
                    }
                });
            }
        };

        const animate = function () {
            requestAnimationFrame(animate);
            rotAngle += 0.002;
            camera.position.x = Math.sin(rotAngle) * 70;
            camera.position.z = Math.cos(rotAngle) * 70;
            camera.lookAt(0, 0, 0);

            const pos = particles.geometry.attributes.position.array;
            for(let i=0; i<1000; i++) {
                pos[i*3+2] += isThinking ? 2.5 : 0.3;
                if(pos[i*3+2] > 50) {
                    pos[i*3] = (Math.random()-0.5)*80;
                    pos[i*3+1] = (Math.random()-0.5)*80;
                    pos[i*3+2] = -50;
                }
            }
            particles.geometry.attributes.position.needsUpdate = true;

            renderer.render(scene, camera);
        };
        animate();

        return () => {
            mountRef.current?.removeChild(renderer.domElement);
            ws.close();
        };
    }, []);

    return (
        <div style={{ position: 'relative', width: '100%', height: '100%', background: '#000' }}>
            <div style={{ position: 'absolute', top: 20, left: 20, padding: 15, border: '1px solid #0ff', background: 'rgba(0,20,20,0.8)', zIndex: 10 }}>
                <h3 style={{ margin: '0 0 10px 0', color: stats.status === 'THINKING...' ? '#f0f' : '#0ff' }}>STATUS: {stats.status}</h3>
                <div style={{ color: '#0ff', fontFamily: 'monospace', fontSize: '1.2em' }}>TOKENS: {stats.tokens}</div>
                <div style={{ color: '#0ff', fontFamily: 'monospace', fontSize: '1.2em' }}>TPS: {stats.tps.toFixed(2)}</div>
                {stats.stream && (
                    <div style={{ marginTop: 10, color: '#fff', maxWidth: '300px', wordWrap: 'break-word', fontFamily: 'monospace' }}>
                        "...{stats.stream.slice(-50)}"
                    </div>
                )}
            </div>
            
            {/* Overlay labels */}
            <div style={{ position: 'absolute', bottom: 40, width: '100%', display: 'flex', justifyContent: 'center', gap: '80px', pointerEvents: 'none', color: '#0ff', opacity: 0.6, fontSize: '24px', fontWeight: 'bold' }}>
                <span>[EMBEDDING]</span>
                <span>[ATTENTION]</span>
                <span>[FEED-FORWARD]</span>
                <span>[OUTPUT]</span>
            </div>

            <div ref={mountRef} style={{ width: '100%', height: '100%' }} />
        </div>
    );
}
