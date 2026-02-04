#!/usr/bin/env python3
"""
Simple test script to verify the webapp server works.

This script:
1. Creates a minimal output directory with sample CSV files
2. Starts the visualization server
3. Opens the browser

Run with: python test_webapp_server.py
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if Flask is installed
try:
    import flask
    print("✓ Flask is installed")
except ImportError:
    print("✗ Flask not installed. Install with: pip install Flask")
    sys.exit(1)

# Try to import our module
try:
    from src.visualization import open_visualization
    print("✓ Visualization module imported successfully")
except Exception as e:
    print(f"✗ Failed to import visualization module: {e}")
    sys.exit(1)

# Check if webapp files exist
webapp_path = Path(__file__).parent / "webapp"
if not webapp_path.exists():
    print(f"✗ Webapp folder not found at {webapp_path}")
    sys.exit(1)

webapp_files = ["index.html", "script.js", "styles.css"]
for file in webapp_files:
    if not (webapp_path / file).exists():
        print(f"✗ Missing {file} in webapp folder")
        sys.exit(1)

print(f"✓ Webapp files found at {webapp_path}")

# Create minimal output directory with sample CSV
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# Create sample edges.csv
edges_csv = output_dir / "edges.csv"
if not edges_csv.exists():
    edges_csv.write_text("""id;source;target;name;maxspeed;nlanes;geometry;coilcode
1;1;2;Via Test;50;2;LINESTRING(11.3426 44.4944 11.3445 44.4956);code1
2;2;3;Via Demo;60;3;LINESTRING(11.3445 44.4956 11.3460 44.4970);code2
""")
    print(f"✓ Created sample edges.csv")
else:
    print(f"✓ edges.csv already exists")

# Create sample densities.csv
densities_csv = output_dir / "densities.csv"
if not densities_csv.exists():
    densities_csv.write_text("""datetime;1;2
2024-01-01 00:00:00;0.5;0.3
2024-01-01 00:05:00;0.6;0.4
2024-01-01 00:10:00;0.7;0.5
""")
    print(f"✓ Created sample densities.csv")
else:
    print(f"✓ densities.csv already exists")

# Create sample data.csv
data_csv = output_dir / "data.csv"
if not data_csv.exists():
    data_csv.write_text("""datetime;mean_density_vpk
2024-01-01 00:00:00;0.4
2024-01-01 00:05:00;0.5
2024-01-01 00:10:00;0.6
""")
    print(f"✓ Created sample data.csv")
else:
    print(f"✓ data.csv already exists")

print("\n" + "="*60)
print("Starting visualization server...")
print("="*60)

# Start visualization
open_visualization(output_dir=str(output_dir), port=8000)

# Keep running
try:
    print("\nServer is running. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nServer stopped.")
