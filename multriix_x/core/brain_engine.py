import time
import random
import threading
import json

class BrainEngine:
    def __init__(self):
        self.is_running = False
        self.current_token = ""
        self.thinking = False
        self.tps = 0.0
        self.token_stream = []
        self.nodes = self._generate_static_nodes()
        self.connections = self._generate_static_connections()
        self.lock = threading.Lock()

    def _generate_static_nodes(self):
        nodes = []
        layers = ["embedding", "attention_1", "ffn_1", "output"]
        for i, layer in enumerate(layers):
            for j in range(10):
                nodes.append({
                    "id": f"n_{i}_{j}",
                    "layer": layer,
                    "x": i * 200,
                    "y": j * 50 - 250,
                    "activation": 0.0
                })
        return nodes

    def _generate_static_connections(self):
        connections = []
        layers = ["embedding", "attention_1", "ffn_1", "output"]
        for i in range(len(layers) - 1):
            for j in range(5): # Sample connections
                from_node = f"n_{i}_{random.randint(0, 9)}"
                to_node = f"n_{i+1}_{random.randint(0, 9)}"
                connections.append({
                    "from": from_node,
                    "to": to_node,
                    "weight": random.random(),
                    "active": False
                })
        return connections

    def get_brain_data(self):
        with self.lock:
            # Update activations randomly if idle, or specifically if generating
            for node in self.nodes:
                if self.thinking:
                    node["activation"] = random.uniform(0.5, 1.0)
                else:
                    node["activation"] = random.uniform(0.0, 0.2)
            
            for conn in self.connections:
                conn["active"] = self.thinking and random.random() > 0.5

            return {
                "timestamp": time.time(),
                "nodes": self.nodes,
                "connections": self.connections,
                "current_token": self.current_token,
                "thinking": self.thinking,
                "tokens_per_second": self.tps,
                "attention_heatmap": [[random.random() for _ in range(5)] for _ in range(5)],
                "token_stream": self.token_stream[-20:],
                "layer_activations": {
                    "embedding": [random.random() for _ in range(10)],
                    "attention_1": [random.random() for _ in range(10)],
                    "ffn_1": [random.random() for _ in range(10)],
                    "output": [random.random() for _ in range(10)]
                }
            }

    def start_generation(self):
        self.thinking = True

    def stop_generation(self):
        self.thinking = False
        self.current_token = ""
        # Keep token stream for a bit, maybe clear later

    def update_token(self, token, tps):
        self.current_token = token
        if token:
            self.token_stream.append(token)
        self.tps = tps
