"""Tactical CAD Local Server [Cut the Cake / M2B].

Minimal, high-performance local web server hosting the Tactical CAD browser workbench
and serving real-time geometric re-analysis requests for arbitrary CADDocument sessions.

Usage:
    python -m cut_the_cake.cad_server --port 5000
"""

from __future__ import annotations
import argparse
import os
import sys
from typing import Dict, Any, Optional

try:
    from flask import Flask, request, jsonify, send_from_directory, Response
except ImportError:
    sys.exit("Error: Flask is required for the CAD server. Install with: pip install -e \".[cad]\"")

from .cad_document import (
    CADDocument,
    get_canonical_f1_document,
    get_custom_asymmetric_corridor_document,
    validate_cad_document
)
from .cad_adapter import (
    analyze_cad_document,
    translate_obstacle_in_document,
    create_rectangle_obstacle,
    resize_rectangle_obstacle,
    rotate_obstacle_in_document,
    delete_obstacle_in_document,
    analyze_candidate_geometry
)
from .cad_export import export_scene_manifest


def create_cad_app() -> Flask:
    """Factory creating configured Flask application for Tactical CAD."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    web_dir = os.path.join(repo_root, "cad", "web")
    data_dir = os.path.join(repo_root, "cad", "data")

    app = Flask(__name__, static_folder=web_dir)

    # In-memory working document session with undo/redo history
    import copy
    active_state = {
        "working_document": get_canonical_f1_document(),
        "baseline_document": get_canonical_f1_document(),
        "document_type": "canonical_f1",
        "undo_stack": [],
        "redo_stack": []
    }

    def push_undo_state():
        """Push a snapshot of working_document onto undo_stack and clear redo_stack."""
        active_state["undo_stack"].append(copy.deepcopy(active_state["working_document"]))
        if len(active_state["undo_stack"]) > 100:
            active_state["undo_stack"].pop(0)
        active_state["redo_stack"].clear()

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
            "version": "2.0-M2C"
        })

    # =========================================================================
    # DOCUMENT SESSION & MUTATION ENDPOINTS (M2C)
    # =========================================================================

    @app.route("/api/document", methods=["GET"])
    def get_document():
        """Retrieve active working CADDocument."""
        doc_dict = active_state["working_document"].to_dict()
        doc_dict["can_undo"] = len(active_state["undo_stack"]) > 0
        doc_dict["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(doc_dict)

    @app.route("/api/document/load", methods=["POST"])
    def load_document():
        """Load a named document template or a validated raw CADDocument JSON."""
        req_data = request.get_json(force=True, silent=True) or {}
        name = req_data.get("name", "").lower()
        
        if name in ("canonical_f1", "f1", "repairpop_f1_staggerdeficit_00"):
            doc = get_canonical_f1_document()
            active_state["document_type"] = "canonical_f1"
        elif name in ("custom_corridor", "custom", "custom_asymmetric_corridor"):
            doc = get_custom_asymmetric_corridor_document()
            active_state["document_type"] = "custom_corridor"
        elif "document" in req_data:
            doc_dict = req_data["document"]
            is_valid, errors = validate_cad_document(doc_dict)
            if not is_valid:
                return jsonify({
                    "error": "Document validation failed.",
                    "details": errors
                }), 422
            doc = CADDocument.from_dict(doc_dict)
            active_state["document_type"] = "custom_upload"
        else:
            return jsonify({"error": f"Unknown document name '{name}'"}), 400

        active_state["baseline_document"] = copy.deepcopy(doc)
        active_state["working_document"] = copy.deepcopy(doc)
        active_state["undo_stack"].clear()
        active_state["redo_stack"].clear()

        return jsonify({
            "status": "loaded",
            "document_type": active_state["document_type"],
            "document": doc.to_dict(),
            "can_undo": False,
            "can_redo": False
        })

    @app.route("/api/document/reset", methods=["POST"])
    def reset_document():
        """Reset active working document to its baseline state."""
        active_state["working_document"] = copy.deepcopy(active_state["baseline_document"])
        active_state["undo_stack"].clear()
        active_state["redo_stack"].clear()
        return jsonify({
            "status": "reset",
            "document": active_state["working_document"].to_dict(),
            "can_undo": False,
            "can_redo": False
        })

    @app.route("/api/document/create_obstacle", methods=["POST"])
    def create_obstacle():
        """Create a new rectangle obstacle in the active working document."""
        req_data = request.get_json(force=True, silent=True) or {}
        x1 = float(req_data.get("x1", 0.0))
        y1 = float(req_data.get("y1", 0.0))
        x2 = float(req_data.get("x2", 0.0))
        y2 = float(req_data.get("y2", 0.0))
        name = req_data.get("name")
        obstacle_id = req_data.get("obstacle_id")
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, new_id, is_valid, error_reason = create_rectangle_obstacle(
            working_doc, x1, y1, x2, y2, obstacle_id=obstacle_id, name=name
        )
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "runtime_ms": 0.0
            }), 422

        if commit:
            push_undo_state()
            active_state["working_document"] = cand_doc

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["created_obstacle_id"] = new_id
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/translate_obstacle", methods=["POST"])
    def translate_obstacle():
        """Generic 2D translation of any obstacle in the active document with cumulative commit support."""
        req_data = request.get_json(force=True, silent=True) or {}
        obstacle_id = req_data.get("obstacle_id")
        dx = float(req_data.get("dx", 0.0))
        dy = float(req_data.get("dy", 0.0))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", False))
        commit = bool(req_data.get("commit", False))
        route_id = req_data.get("route_id")

        if not obstacle_id:
            return jsonify({
                "is_valid": False,
                "error_reason": "Missing 'obstacle_id' parameter.",
                "client_revision": client_revision
            }), 400

        # Translate relative to current working document
        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = translate_obstacle_in_document(working_doc, obstacle_id, dx, dy)
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "dx": dx,
                "dy": dy,
                "runtime_ms": 0.0
            }), 422

        if commit:
            push_undo_state()
            active_state["working_document"] = cand_doc

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["dx"] = dx
        res["dy"] = dy
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/resize_obstacle", methods=["POST"])
    def resize_obstacle():
        """Resize a rectangle obstacle by dragging a corner handle."""
        req_data = request.get_json(force=True, silent=True) or {}
        obstacle_id = req_data.get("obstacle_id")
        handle = req_data.get("handle", "se")
        dx = float(req_data.get("dx", 0.0))
        dy = float(req_data.get("dy", 0.0))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", False))
        commit = bool(req_data.get("commit", False))
        route_id = req_data.get("route_id")

        if not obstacle_id:
            return jsonify({
                "is_valid": False,
                "error_reason": "Missing 'obstacle_id' parameter.",
                "client_revision": client_revision
            }), 400

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = resize_rectangle_obstacle(
            working_doc, obstacle_id, handle, dx, dy
        )
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "dx": dx,
                "dy": dy,
                "runtime_ms": 0.0
            }), 422

        if commit:
            push_undo_state()
            active_state["working_document"] = cand_doc

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["obstacle_id"] = obstacle_id
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/rotate_obstacle", methods=["POST"])
    def rotate_obstacle():
        """Rotate an obstacle by angle_deg around its centroid."""
        req_data = request.get_json(force=True, silent=True) or {}
        obstacle_id = req_data.get("obstacle_id")
        angle_deg = float(req_data.get("angle_deg", 0.0))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", False))
        commit = bool(req_data.get("commit", False))
        route_id = req_data.get("route_id")

        if not obstacle_id:
            return jsonify({
                "is_valid": False,
                "error_reason": "Missing 'obstacle_id' parameter.",
                "client_revision": client_revision
            }), 400

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = rotate_obstacle_in_document(
            working_doc, obstacle_id, angle_deg
        )
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "angle_deg": angle_deg,
                "runtime_ms": 0.0
            }), 422

        if commit:
            push_undo_state()
            active_state["working_document"] = cand_doc

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["obstacle_id"] = obstacle_id
        res["angle_deg"] = angle_deg
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/delete_obstacle", methods=["POST"])
    def delete_obstacle():
        """Delete an obstacle from the working document."""
        req_data = request.get_json(force=True, silent=True) or {}
        obstacle_id = req_data.get("obstacle_id")
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        route_id = req_data.get("route_id")

        if not obstacle_id:
            return jsonify({
                "is_valid": False,
                "error_reason": "Missing 'obstacle_id' parameter.",
                "client_revision": client_revision
            }), 400

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = delete_obstacle_in_document(working_doc, obstacle_id)
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "runtime_ms": 0.0
            }), 422

        push_undo_state()
        active_state["working_document"] = cand_doc

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["deleted_obstacle_id"] = obstacle_id
        res["is_committed"] = True
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/undo", methods=["POST"])
    def undo_document():
        """Restore previous document snapshot from undo stack."""
        if not active_state["undo_stack"]:
            return jsonify({"error": "Nothing to undo", "can_undo": False, "can_redo": len(active_state["redo_stack"]) > 0}), 400

        req_data = request.get_json(force=True, silent=True) or {}
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        route_id = req_data.get("route_id")

        prev_doc = active_state["undo_stack"].pop()
        active_state["redo_stack"].append(copy.deepcopy(active_state["working_document"]))
        active_state["working_document"] = prev_doc

        res = analyze_cad_document(
            doc=prev_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        res["is_committed"] = True
        return jsonify(res), 200

    @app.route("/api/document/redo", methods=["POST"])
    def redo_document():
        """Restore next document snapshot from redo stack."""
        if not active_state["redo_stack"]:
            return jsonify({"error": "Nothing to redo", "can_undo": len(active_state["undo_stack"]) > 0, "can_redo": False}), 400

        req_data = request.get_json(force=True, silent=True) or {}
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        route_id = req_data.get("route_id")

        next_doc = active_state["redo_stack"].pop()
        active_state["undo_stack"].append(copy.deepcopy(active_state["working_document"]))
        active_state["working_document"] = next_doc

        res = analyze_cad_document(
            doc=next_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        res["is_committed"] = True
        return jsonify(res), 200

    @app.route("/api/document/analyze", methods=["POST"])
    def analyze_document():
        """Analyze arbitrary CADDocument payload or the active working document."""
        req_data = request.get_json(force=True, silent=True) or {}
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", False))
        route_id = req_data.get("route_id")

        if "document" in req_data:
            doc_dict = req_data["document"]
            is_valid, errors = validate_cad_document(doc_dict)
            if not is_valid:
                return jsonify({
                    "is_valid": False,
                    "error_reason": f"Document validation failed: {'; '.join(errors)}",
                    "details": errors,
                    "client_revision": client_revision
                }), 422
            doc = CADDocument.from_dict(doc_dict)
        else:
            doc = active_state["working_document"]

        res = analyze_cad_document(
            doc=doc,
            route_id=route_id,
            include_telemetry=include_telemetry,
            client_revision=client_revision
        )
        return jsonify(res), (200 if res.get("is_valid", False) else 422)

    # =========================================================================
    # BACKWARD COMPATIBILITY ENDPOINTS (M2A / M1)
    # =========================================================================

    @app.route("/api/fixture/<fixture_id>", methods=["GET"])
    def get_fixture(fixture_id):
        try:
            manifest = export_scene_manifest(fixture_id=fixture_id)
            return jsonify(manifest)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/analyze", methods=["POST"])
    def analyze_legacy():
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
    print(f"🍰 Cut the Cake / Tactical CAD Server (M2B) running at http://{args.host}:{args.port}/")
    print("   Serving CAD Workbench with arbitrary CADDocument session & 2D translation.")
    print("=" * 70)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
