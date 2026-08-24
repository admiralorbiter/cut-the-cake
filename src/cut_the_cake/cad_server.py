"""Tactical CAD Local Server [Cut the Cake / M2A].

Minimal, high-performance local web server hosting the Tactical CAD browser workbench
and serving real-time geometric re-analysis requests.

Usage:
    python -m cut_the_cake.cad_server --port 5000
"""

from __future__ import annotations
import argparse
import os
import sys
from typing import Dict, Any

try:
    from flask import Flask, request, jsonify, send_from_directory, Response
except ImportError:
    sys.exit("Error: Flask is required for the CAD server. Install with: pip install -e \".[cad]\"")

from .cad_adapter import analyze_candidate_geometry
from .cad_export import export_scene_manifest


def create_cad_app() -> Flask:
    """Factory creating configured Flask application for Tactical CAD."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    web_dir = os.path.join(repo_root, "cad", "web")
    data_dir = os.path.join(repo_root, "cad", "data")

    app = Flask(__name__, static_folder=web_dir)

    # Disable strict slashes
    app.url_map.strict_slashes = False

    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(web_dir, "index.html")

    @app.route("/data/<path:filename>", methods=["GET"])
    def serve_data(filename):
        return send_from_directory(data_dir, filename)

    @app.route("/<path:filename>", methods=["GET"])
    def serve_static(filename):
        if os.path.exists(os.path.join(web_dir, filename)):
            return send_from_directory(web_dir, filename)
        if os.path.exists(os.path.join(data_dir, filename)):
            return send_from_directory(data_dir, filename)
        return jsonify({"error": f"File '{filename}' not found."}), 404

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "service": "Cut the Cake Tactical CAD Server",
            "version": "1.1"
        })

    @app.route("/api/fixture/<fixture_id>", methods=["GET"])
    def get_fixture(fixture_id):
        try:
            manifest = export_scene_manifest(fixture_id=fixture_id)
            return jsonify(manifest)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        req_data = request.get_json(force=True, silent=True) or {}
        
        fixture_id = req_data.get("fixture_id", "RepairPop_F1_StaggerDeficit_00")
        obstacle_id = int(req_data.get("obstacle_id", 0))
        translation_m = float(req_data.get("translation_m", 0.0))
        axis = str(req_data.get("axis", "x"))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", False))

        res = analyze_candidate_geometry(
            fixture_id=fixture_id,
            obstacle_id=obstacle_id,
            translation_m=translation_m,
            axis=axis,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )

        return jsonify(res), (200 if res.get("is_valid", False) else 422)

    return app


def main():
    parser = argparse.ArgumentParser(description="Cut the Cake - Tactical CAD Local Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    app = create_cad_app()
    print("=" * 70)
    print(f"🍰 Cut the Cake / Tactical CAD Server running at http://{args.host}:{args.port}/")
    print("   Serving CAD Workbench with real-time Python geometric re-analysis.")
    print("=" * 70)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
