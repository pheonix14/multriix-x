import socket
import os

class PortManager:
    def __init__(self, start_port=7860, max_port=7900):
        self.start_port = start_port
        self.max_port = max_port
        self.port_file = ".multriix_port"

    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def find_free_port(self):
        for port in range(self.start_port, self.max_port + 1):
            if not self.is_port_in_use(port):
                if port != self.start_port:
                    print(f"Port {self.start_port} busy → switching to {port} ✅")
                self.save_port(port)
                return port
        raise IOError(f"No free ports found in range {self.start_port}-{self.max_port}")

    def save_port(self, port):
        with open(self.port_file, "w") as f:
            f.write(str(port))

    def get_saved_port(self):
        if os.path.exists(self.port_file):
            with open(self.port_file, "r") as f:
                return int(f.read().strip())
        return self.start_port
