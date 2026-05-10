// MULTRIIX X - Advanced Live Brain Renderer (Vanilla Three.js)

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('brain-container');
    if (!container) return;

    // SCENE SETUP
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x000505, 0.05);

    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 20, 60);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // ORBIT CONTROLS (simulated auto-rotation if no user input)
    let angle = 0;

    // GROUPS
    const networkGroup = new THREE.Group();
    const heatmapGroup = new THREE.Group();
    const particleGroup = new THREE.Group();
    scene.add(networkGroup);
    scene.add(heatmapGroup);
    scene.add(particleGroup);

    // MATERIALS
    const nodeMatInactive = new THREE.MeshBasicMaterial({ color: 0x008888, transparent: true, opacity: 0.6 });
    const nodeMatActive = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1.0 });
    const nodeMatHighAttn = new THREE.MeshBasicMaterial({ color: 0xff8800, transparent: true, opacity: 1.0 });
    
    const lineMatInactive = new THREE.LineBasicMaterial({ color: 0x004444, transparent: true, opacity: 0.2 });
    const lineMatActive = new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.8 });

    // LAYERS MAPPING
    const layerNames = ["EMBED", "ATTN", "FFN", "OUT"];
    const layerZ = { "embedding": -30, "attention_1": -10, "ffn_1": 10, "output": 30 };

    // CACHE
    let nodeMeshes = {};
    let lineLines = [];

    // PARTICLES (Tokens)
    const particleGeo = new THREE.BufferGeometry();
    const particleCount = 1000;
    const particlePos = new Float32Array(particleCount * 3);
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    const particleMat = new THREE.PointsMaterial({ color: 0x00ffff, size: 0.5, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending });
    const particles = new THREE.Points(particleGeo, particleMat);
    particleGroup.add(particles);

    // LABELS (Canvas Text)
    function createLabel(text, position) {
        const canvas = document.createElement('canvas');
        canvas.width = 256; canvas.height = 64;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#00ffff';
        ctx.font = '32px Courier New';
        ctx.textAlign = 'center';
        ctx.fillText(text, 128, 48);
        const tex = new THREE.CanvasTexture(canvas);
        const mat = new THREE.SpriteMaterial({ map: tex, transparent: true });
        const sprite = new THREE.Sprite(mat);
        sprite.position.copy(position);
        sprite.scale.set(20, 5, 1);
        scene.add(sprite);
    }
    
    Object.keys(layerZ).forEach((k, i) => {
        createLabel(layerNames[i], new THREE.Vector3(-40, 25, layerZ[k]));
    });

    // WEBSOCKET
    let isThinking = false;
    const ws = new WebSocket(`ws://${window.location.host}/ws/brain`);
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        isThinking = data.thinking;

        // UI Updates
        document.getElementById('brain-status').innerText = isThinking ? 'THINKING...' : 'IDLE';
        document.getElementById('brain-status').style.color = isThinking ? '#ff00ff' : '#00ffff';
        document.getElementById('brain-tps').innerText = data.tokens_per_second ? data.tokens_per_second.toFixed(2) : '0.00';
        document.getElementById('brain-tokens').innerText = data.token_stream ? data.token_stream.length : 0;

        // Create/Update Nodes
        data.nodes.forEach(n => {
            if (!nodeMeshes[n.id]) {
                const geo = new THREE.SphereGeometry(1, 16, 16);
                const mesh = new THREE.Mesh(geo, nodeMatInactive);
                mesh.position.set(n.x / 10 - 10, n.y / 10, layerZ[n.layer] || 0);
                networkGroup.add(mesh);
                nodeMeshes[n.id] = mesh;
            }
            const m = nodeMeshes[n.id];
            if (n.activation > 0.8) m.material = nodeMatHighAttn;
            else if (n.activation > 0.3) m.material = nodeMatActive;
            else m.material = nodeMatInactive;
            
            const scale = 1 + n.activation;
            m.scale.set(scale, scale, scale);
        });

        // Rebuild Connections if active
        // Simplification for performance: we update materials instead of rebuilding lines
        while(networkGroup.children.length > data.nodes.length) {
            const child = networkGroup.children[networkGroup.children.length-1];
            if (child.type === 'Line') networkGroup.remove(child);
            else break;
        }

        if (isThinking && data.connections) {
            // Draw a few active connections
            data.connections.filter(c => c.active).slice(0, 50).forEach(c => {
                const p1 = nodeMeshes[c.from]?.position;
                const p2 = nodeMeshes[c.to]?.position;
                if (p1 && p2) {
                    const geo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
                    const line = new THREE.Line(geo, lineMatActive);
                    networkGroup.add(line);
                    setTimeout(() => networkGroup.remove(line), 100); // Electricity zap effect
                }
            });
        }
    };

    // ANIMATION LOOP
    function animate() {
        requestAnimationFrame(animate);
        
        // Auto-rotate
        angle += 0.002;
        camera.position.x = Math.sin(angle) * 60;
        camera.position.z = Math.cos(angle) * 60;
        camera.lookAt(0, 0, 0);

        // Particle stream effect
        const positions = particles.geometry.attributes.position.array;
        for(let i=0; i<particleCount; i++) {
            positions[i*3+2] += isThinking ? 2.0 : 0.2; // Flow along Z
            if (positions[i*3+2] > 40) {
                positions[i*3] = (Math.random() - 0.5) * 40;
                positions[i*3+1] = (Math.random() - 0.5) * 40;
                positions[i*3+2] = -40;
            }
        }
        particles.geometry.attributes.position.needsUpdate = true;

        renderer.render(scene, camera);
    }

    animate();

    // RESIZE
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
});
