import urllib.request
from pathlib import Path

out_dir = Path("tools/fps_clearability/human_web/lib")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "three.min.js"

url = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
print(f"Downloading Three.js r128 from {url}...")
try:
    urllib.request.urlretrieve(url, out_file)
    print(f"Saved Three.js locally to {out_file} ({out_file.stat().st_size} bytes)")
except Exception as e:
    print(f"Warning: Could not download Three.js locally: {e}")
