import os
import sys
import time
import webbrowser

# Change to multriix_x directory where the real logic lives
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "multriix_x"))
sys.path.insert(0, os.getcwd())

from core.port_manager import PortManager

def main():
    print("""
  ============================================================
  AI CONTROL CENTER  |  PHEONIX14 
  ============================================================""")

    # The user requested port 3000
    pm = PortManager(start_port=3000, max_port=3050)
    port = pm.find_free_port()

    print(f"\n[INFO] Launching Local AI Manager on port {port}...\n")
    
    # Open the browser automatically
    webbrowser.open(f"http://localhost:{port}/frontend/index.html")

    # Start the FastAPI server using uvicorn
    import uvicorn
    from server import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    main()
