"""
Flask server wrapper for webapp visualization.

This module starts a lightweight Flask server that serves the webapp files
and opens a browser window to display the visualization.
"""

from flask import Flask, send_from_directory, redirect
import webbrowser
import threading
import time
from pathlib import Path


def open_visualization(db_path: str, port: int = 8000, auto_open: bool = True):
    """
    Start Flask server and open webapp visualization in browser.
    
    Args:
        db_path: Path to the SQLite database file containing simulation results
        port: Port to run Flask server on (default: 8000)
        auto_open: Whether to automatically open browser (default: True)
    
    Returns:
        None (runs in background thread)
    
    Example:
        >>> from src.visualization import open_visualization
        >>> open_visualization(db_path="./output_20240101_120000/database.db")
    """
    
    # Get absolute path to webapp folder
    webapp_path = Path(__file__).parent.parent.parent / "db_webapp"
    
    if not webapp_path.exists():
        print(f"ERROR: Webapp folder not found at {webapp_path}")
        return
    
    # Resolve the database path
    resolved_db_path = Path(db_path).resolve()
    if not resolved_db_path.exists():
        print(f"ERROR: Database file not found at {resolved_db_path}")
        return
    
    print(f">>> Webapp folder: {webapp_path}")
    print(f">>> Database file: {resolved_db_path}")
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=str(webapp_path),
        static_url_path=""
    )
    
    # Store database path for route handlers
    db_dir = resolved_db_path.parent
    db_filename = resolved_db_path.name
    
    # Route to serve main index with database path as URL parameter
    @app.route("/")
    def index():
        """Serve main HTML file with database path as URL parameter"""
        return redirect(f"/index.html?db=/db/{db_filename}")
    
    # Route to serve database files from the output directory
    @app.route("/db/<path:filename>")
    def serve_db_files(filename):
        """Serve database files from the output directory"""
        print(f">>> Serving database file: {filename} from {db_dir}")
        return send_from_directory(str(db_dir), filename)
    
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
