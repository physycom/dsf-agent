"""
Flask server wrapper for webapp visualization.

This module starts a lightweight Flask server that serves the webapp files
and opens a browser window to display the visualization.
"""

from flask import Flask, send_from_directory, jsonify
import webbrowser
import threading
import time
import os
from pathlib import Path


def open_visualization(output_dir: str = "./output", port: int = 8000, auto_open: bool = True):
    """
    Start Flask server and open webapp visualization in browser.
    
    Args:
        output_dir: Path to directory containing CSV data files (edges.csv, densities.csv, data.csv)
        port: Port to run Flask server on (default: 8000)
        auto_open: Whether to automatically open browser (default: True)
    
    Returns:
        None (runs in background thread)
    
    Example:
        >>> from src.visualization import open_visualization
        >>> open_visualization(output_dir="./output")
    """
    
    # Get absolute path to webapp folder
    webapp_path = Path(__file__).parent.parent.parent / "webapp"
    
    if not webapp_path.exists():
        print(f"ERROR: Webapp folder not found at {webapp_path}")
        return
    
    print(f">>> Webapp folder: {webapp_path}")
    print(f">>> Output data directory: {Path(output_dir).resolve()}")
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=str(webapp_path),
        static_url_path=""
    )
    
    # Route to serve main index
    @app.route("/")
    def index():
        """Serve main HTML file"""
        return send_from_directory(app.static_folder, "index.html")
    
    # Route to serve dynamic config.json based on output_dir parameter
    @app.route("/config.json")
    def serve_config():
        """Serve config.json dynamically based on output_dir parameter"""
        # Create config with /data/ prefix (Flask will serve from output_dir)
        config = {
            "serverRoot": str(Path.cwd()),
            "edges": "/data/edges.csv",
            "densities": "/data/densities.csv",
            "data": "/data/data.csv"
        }
        
        print(f">>> Serving config.json - data will be served from: {Path(output_dir).resolve()}")
        
        return jsonify(config)
    
    # Route to serve CSV files from output directory (dynamic based on output_dir parameter)
    @app.route("/data/<path:filename>")
    def serve_data_files(filename):
        """Serve CSV files from the output directory specified in output_dir parameter"""
        output_path = Path(output_dir).resolve()
        print(f">>> Serving file: {filename} from {output_path}")
        return send_from_directory(str(output_path), filename)
    
    # Route to serve static files (CSS, JS)
    @app.route("/<path:filename>")
    def serve_static(filename):
        """Serve static files (CSS, JS, etc)"""
        return send_from_directory(app.static_folder, filename)
    
    # Start server in daemon thread
    def run_server():
        try:
            print(f"\n>>> Starting Flask server on http://localhost:{port}")
            app.run(
                host="127.0.0.1",
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            print(f"ERROR: Failed to start Flask server: {e}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server a moment to start
    time.sleep(1)
    
    # Open browser
    if auto_open:
        try:
            url = f"http://localhost:{port}/"
            print(f">>> Opening browser at {url}")
            webbrowser.open(url)
        except Exception as e:
            print(f"ERROR: Failed to open browser: {e}")
            print(f">>> You can manually open: http://localhost:{port}/")
    
    print("\n>>> Visualization server is running")
    print(">>> Press Ctrl+C to stop the server\n")


if __name__ == "__main__":
    open_visualization()
