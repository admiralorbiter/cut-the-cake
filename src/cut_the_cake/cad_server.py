"""Tactical CAD Local Server [Cut the Cake / M2B].

Minimal, high-performance local web server hosting the Tactical CAD browser workbench
and serving real-time geometric re-analysis requests for arbitrary CADDocument sessions.

Usage:
    python -m cut_the_cake.cad_server --port 5000
"""

from __future__ import annotations
import argparse
import hashlib
import json
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
    get_dust2_a_long_document,
    get_ascent_a_main_document,
    get_dust2_b_tunnels_document,
    get_transit_213_document,
    validate_cad_document
)
from .cad_adapter import (
    analyze_cad_document,
    translate_obstacle_in_document,
    create_rectangle_obstacle,
    resize_rectangle_obstacle,
    rotate_obstacle_in_document,
    delete_obstacle_in_document,
    analyze_candidate_geometry,
    create_route_in_document,
    update_route_waypoint,
    add_route_waypoint,
    delete_route_waypoint,
    delete_route_in_document,
    update_route_speed,
    create_threat_in_document,
    translate_threat_in_document,
    update_threat_geometry,
    update_threat_due_window,
    update_threat_service_duration,
    delete_threat_in_document,
    update_player_model,
    auto_fix_cad_document,
    compute_cad_route_spatial_heatmap,
    compute_arena_floor_los_exposure
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
    def compute_initial_wall_sequence(doc: CADDocument) -> int:
        max_seq = 0
        for obs in doc.obstacles:
            if obs.id.startswith("wall_"):
                try:
                    seq = int(obs.id.split("_")[1])
                    max_seq = max(max_seq, seq)
                except (ValueError, IndexError):
                    pass
        return max_seq + 1

    def compute_initial_route_sequence(doc: CADDocument) -> int:
        max_seq = 0
        for r in doc.routes:
            if r.id.startswith("route_"):
                try:
                    seq = int(r.id.split("_")[1])
                    max_seq = max(max_seq, seq)
                except (ValueError, IndexError):
                    pass
        return max_seq + 1

    def compute_initial_threat_sequence(doc: CADDocument) -> int:
        max_seq = 0
        for t in doc.threats:
            if t.id.startswith("T"):
                try:
                    seq = int(t.id[1:])
                    max_seq = max(max_seq, seq)
                except (ValueError, IndexError):
                    pass
            elif t.id.startswith("threat_"):
                try:
                    seq = int(t.id.split("_")[1])
                    max_seq = max(max_seq, seq)
                except (ValueError, IndexError):
                    pass
        return max_seq + 1

    active_state = {
        "working_document": get_canonical_f1_document(),
        "baseline_document": get_canonical_f1_document(),
        "document_type": "canonical_f1",
        "undo_stack": [],
        "redo_stack": [],
        "next_wall_sequence": compute_initial_wall_sequence(get_canonical_f1_document()),
        "next_route_sequence": compute_initial_route_sequence(get_canonical_f1_document()),
        "next_threat_sequence": compute_initial_threat_sequence(get_canonical_f1_document())
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
            "version": "2.0-M2D"
        })

    # =========================================================================
    # DOCUMENT SESSION & MUTATION ENDPOINTS (M2C / M2D)
    # =========================================================================

    @app.route("/api/document", methods=["GET"])
    def get_document():
        """Retrieve active working CADDocument."""
        doc = active_state["working_document"]
        doc_dict = doc.to_dict()
        doc_dict["hash"] = compute_document_hash(doc)
        doc_dict["can_undo"] = len(active_state["undo_stack"]) > 0
        doc_dict["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(doc_dict)

    @app.route("/api/document/load", methods=["POST"])
    def load_document():
        """Load a named document template or a validated raw CADDocument JSON."""
        req_data = request.get_json(force=True, silent=True) or {}
        name = req_data.get("name", "").lower()
        
        if name in ("canonical_f1", "f1", "canonical"):
            doc = get_canonical_f1_document()
            active_state["document_type"] = "canonical_f1"
        elif name in ("custom_corridor", "custom", "custom_asymmetric_corridor"):
            doc = get_custom_asymmetric_corridor_document()
            active_state["document_type"] = "custom_corridor"
        elif name in ("dust2_a_long", "dust2", "dust_2", "dustii"):
            doc = get_dust2_a_long_document()
            active_state["document_type"] = "dust2_a_long"
        elif name in ("ascent_a_main", "ascent", "ascent_a"):
            doc = get_ascent_a_main_document()
            active_state["document_type"] = "ascent_a_main"
        elif name in ("dust2_b_tunnels", "dust2_b", "dust2_tunnels", "b_tunnels"):
            doc = get_dust2_b_tunnels_document()
            active_state["document_type"] = "dust2_b_tunnels"
        elif name in ("transit_213", "transit", "transit213"):
            doc = get_transit_213_document()
            active_state["document_type"] = "transit_213"
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
        active_state["next_wall_sequence"] = compute_initial_wall_sequence(doc)
        active_state["next_route_sequence"] = compute_initial_route_sequence(doc)
        active_state["next_threat_sequence"] = compute_initial_threat_sequence(doc)

        doc_payload = doc.to_dict()
        doc_payload["hash"] = compute_document_hash(doc)

        return jsonify({
            "status": "loaded",
            "document_type": active_state["document_type"],
            "document": doc_payload,
            "can_undo": False,
            "can_redo": False
        })

    @app.route("/api/document/reset", methods=["POST"])
    def reset_document():
        """Reset active working document to its baseline state."""
        active_state["working_document"] = copy.deepcopy(active_state["baseline_document"])
        active_state["undo_stack"].clear()
        active_state["redo_stack"].clear()
        doc_payload = active_state["working_document"].to_dict()
        doc_payload["hash"] = compute_document_hash(active_state["working_document"])
        return jsonify({
            "status": "reset",
            "document": doc_payload,
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
            working_doc, x1, y1, x2, y2,
            obstacle_id=obstacle_id,
            name=name,
            session_sequence=active_state["next_wall_sequence"]
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
            if not obstacle_id and new_id and new_id.startswith("wall_"):
                try:
                    num = int(new_id.split("_")[1])
                    active_state["next_wall_sequence"] = max(active_state["next_wall_sequence"], num + 1)
                except (ValueError, IndexError):
                    active_state["next_wall_sequence"] += 1

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
        """Rotate an obstacle by delta or to target orientation angle around its centroid."""
        req_data = request.get_json(force=True, silent=True) or {}
        obstacle_id = req_data.get("obstacle_id")
        target_angle = req_data.get("target_angle_deg")
        if target_angle is None:
            target_angle = req_data.get("absolute_angle_deg")
        angle_delta = req_data.get("angle_delta_deg")
        if angle_delta is None and target_angle is None:
            angle_delta = req_data.get("angle_deg", 0.0)

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
            working_doc, obstacle_id,
            angle_delta_deg=float(angle_delta) if angle_delta is not None else None,
            target_angle_deg=float(target_angle) if target_angle is not None else None
        )
        if not is_valid:
            return jsonify({
                "is_valid": False,
                "error_reason": error_reason,
                "client_revision": client_revision,
                "angle_delta_deg": angle_delta,
                "target_angle_deg": target_angle,
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
        res["angle_deg"] = angle_delta if angle_delta is not None else target_angle
        res["angle_delta_deg"] = angle_delta
        res["target_angle_deg"] = target_angle
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

    # =========================================================================
    # M2D ROUTE MUTATION ENDPOINTS
    # =========================================================================

    @app.route("/api/document/create_route", methods=["POST"])
    def create_route():
        """Create a new authored route in the working document."""
        req_data = request.get_json(force=True, silent=True) or {}
        waypoints = req_data.get("waypoints", [])
        name = req_data.get("name")
        route_id = req_data.get("route_id")
        v_move_mps = float(req_data.get("v_move_mps", 4.5))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))

        working_doc = active_state["working_document"]
        cand_doc, cand_id, is_valid, error_reason = create_route_in_document(
            doc=working_doc,
            route_id=route_id,
            name=name,
            waypoints=waypoints,
            v_move_mps=v_move_mps,
            session_sequence=active_state["next_route_sequence"]
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
            if route_id is None:
                active_state["next_route_sequence"] += 1

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=cand_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["created_route_id"] = cand_id
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/update_route_waypoint", methods=["POST"])
    def update_route_wpt():
        """Update an individual waypoint position on a route."""
        req_data = request.get_json(force=True, silent=True) or {}
        route_id = req_data.get("route_id")
        waypoint_idx = int(req_data.get("waypoint_idx", -1))
        x = float(req_data.get("x", 0.0))
        y = float(req_data.get("y", 0.0))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = update_route_waypoint(working_doc, route_id, waypoint_idx, x, y)
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
        res["route_id"] = route_id
        res["waypoint_idx"] = waypoint_idx
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/add_route_waypoint", methods=["POST"])
    def add_route_wpt():
        """Add a new waypoint to a route."""
        req_data = request.get_json(force=True, silent=True) or {}
        route_id = req_data.get("route_id")
        x = float(req_data.get("x", 0.0))
        y = float(req_data.get("y", 0.0))
        insert_idx = req_data.get("insert_idx")
        if insert_idx is not None:
            insert_idx = int(insert_idx)
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = add_route_waypoint(working_doc, route_id, x, y, insert_idx)
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
        res["route_id"] = route_id
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/delete_route_waypoint", methods=["POST"])
    def delete_route_wpt():
        """Delete a waypoint from a route."""
        req_data = request.get_json(force=True, silent=True) or {}
        route_id = req_data.get("route_id")
        waypoint_idx = int(req_data.get("waypoint_idx", -1))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = delete_route_waypoint(working_doc, route_id, waypoint_idx)
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
        res["route_id"] = route_id
        res["is_committed"] = True
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/delete_route", methods=["POST"])
    def delete_route():
        """Delete an authored route."""
        req_data = request.get_json(force=True, silent=True) or {}
        route_id = req_data.get("route_id")
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = delete_route_in_document(working_doc, route_id)
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
            route_id=None,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["deleted_route_id"] = route_id
        res["is_committed"] = True
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/update_route_speed", methods=["POST"])
    def update_route_spd():
        """Update traversal speed of a route."""
        req_data = request.get_json(force=True, silent=True) or {}
        route_id = req_data.get("route_id")
        v_move_mps = float(req_data.get("v_move_mps", 4.5))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = update_route_speed(working_doc, route_id, v_move_mps)
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
        res["route_id"] = route_id
        res["v_move_mps"] = v_move_mps
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    # =========================================================================
    # M2D THREAT MUTATION ENDPOINTS
    # =========================================================================

    @app.route("/api/document/create_threat", methods=["POST"])
    def create_threat():
        """Create a new threat with anchor and authored region."""
        req_data = request.get_json(force=True, silent=True) or {}
        anchor = req_data.get("anchor")
        polygon = req_data.get("polygon")
        name = req_data.get("name")
        threat_id = req_data.get("threat_id")
        due_window_s = float(req_data.get("due_window_s", 0.62))
        service_duration_s = float(req_data.get("service_duration_s", 0.1143))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, cand_id, is_valid, error_reason = create_threat_in_document(
            doc=working_doc,
            threat_id=threat_id,
            name=name,
            anchor=anchor,
            polygon=polygon,
            due_window_s=due_window_s,
            service_duration_s=service_duration_s,
            session_sequence=active_state["next_threat_sequence"]
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
            if threat_id is None:
                active_state["next_threat_sequence"] += 1

        res = analyze_cad_document(
            doc=cand_doc,
            route_id=route_id,
            client_revision=client_revision,
            include_telemetry=include_telemetry
        )
        res["created_threat_id"] = cand_id
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/translate_threat", methods=["POST"])
    def translate_threat():
        """Translate a threat anchor and region in 2D."""
        req_data = request.get_json(force=True, silent=True) or {}
        threat_id = req_data.get("threat_id")
        dx = float(req_data.get("dx", 0.0))
        dy = float(req_data.get("dy", 0.0))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = translate_threat_in_document(working_doc, threat_id, dx, dy)
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
        res["threat_id"] = threat_id
        res["dx"] = dx
        res["dy"] = dy
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/update_threat_due_window", methods=["POST"])
    def update_threat_dw():
        """Update due window (Delta Dj) of a threat."""
        req_data = request.get_json(force=True, silent=True) or {}
        threat_id = req_data.get("threat_id")
        due_window_s = float(req_data.get("due_window_s", 0.62))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = update_threat_due_window(working_doc, threat_id, due_window_s)
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
        res["threat_id"] = threat_id
        res["due_window_s"] = due_window_s
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/update_threat_service_duration", methods=["POST"])
    def update_threat_sd():
        """Update service duration (sj) of a threat."""
        req_data = request.get_json(force=True, silent=True) or {}
        threat_id = req_data.get("threat_id")
        service_duration_s = float(req_data.get("service_duration_s", 0.1143))
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = update_threat_service_duration(working_doc, threat_id, service_duration_s)
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
        res["threat_id"] = threat_id
        res["service_duration_s"] = service_duration_s
        res["is_committed"] = commit
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/delete_threat", methods=["POST"])
    def delete_threat():
        """Delete a threat from the active working document."""
        req_data = request.get_json(force=True, silent=True) or {}
        threat_id = req_data.get("threat_id")
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = delete_threat_in_document(working_doc, threat_id)
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
        res["deleted_threat_id"] = threat_id
        res["is_committed"] = True
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    # =========================================================================
    # SCENARIO / PLAYER MODEL ENDPOINT
    # =========================================================================

    @app.route("/api/document/update_player_model", methods=["POST"])
    def update_pm():
        """Update player movement, slewing, and initial reticle heading."""
        req_data = request.get_json(force=True, silent=True) or {}
        initial_reticle_deg = req_data.get("initial_reticle_deg")
        v_move_mps = req_data.get("v_move_mps")
        omega_slew_deg_per_s = req_data.get("omega_slew_deg_per_s")
        acquisition_latency_s = req_data.get("acquisition_latency_s")
        service_duration_s = req_data.get("service_duration_s")
        client_revision = int(req_data.get("client_revision", 0))
        include_telemetry = bool(req_data.get("include_telemetry", True))
        commit = bool(req_data.get("commit", True))
        route_id = req_data.get("route_id")

        working_doc = active_state["working_document"]
        cand_doc, is_valid, error_reason = update_player_model(
            doc=working_doc,
            initial_reticle_deg=float(initial_reticle_deg) if initial_reticle_deg is not None else None,
            v_move_mps=float(v_move_mps) if v_move_mps is not None else None,
            omega_slew_deg_per_s=float(omega_slew_deg_per_s) if omega_slew_deg_per_s is not None else None,
            acquisition_latency_s=float(acquisition_latency_s) if acquisition_latency_s is not None else None,
            service_duration_s=float(service_duration_s) if service_duration_s is not None else None
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
        res["player_model"] = cand_doc.player_model.to_dict()
        res["is_committed"] = commit
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

    def compute_document_hash(doc: CADDocument) -> str:
        serialized = json.dumps(doc.to_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    @app.route("/api/document/auto_fix", methods=["POST"])
    def auto_fix_document():
        """Compute grid-minimal Auto-Fix repair for the active working document (M2E).
        
        Optional request parameters:
        - target_margin_tics: int = 2
        - max_perturbation_m: float = 2.0
        - search_resolution_m: float = 0.05
        - route_id: Optional[str]
        - commit: bool = False (if True and repair succeeds, applies to working_document with undo snapshot)
        - expected_doc_hash: Optional[str] (if provided on commit, fails closed with 409 if document was modified)
        """
        req_data = request.get_json(force=True, silent=True) or {}
        target_margin = int(req_data.get("target_margin_tics", 2))
        max_perturbation = float(req_data.get("max_perturbation_m", 2.0))
        search_res = float(req_data.get("search_resolution_m", 0.05))
        route_id = req_data.get("route_id")
        commit = bool(req_data.get("commit", False))
        expected_doc_hash = req_data.get("expected_doc_hash")

        current_hash = compute_document_hash(active_state["working_document"])

        # Fail-closed stale proposal check on commit
        if commit and expected_doc_hash is not None and expected_doc_hash != current_hash:
            return jsonify({
                "success": False,
                "status": "STALE_REPAIR_PROPOSAL",
                "error_reason": (
                    f"Document has changed (current hash {current_hash}) since proposal was generated "
                    f"(expected hash {expected_doc_hash}). Repair proposal is stale and cannot be applied."
                ),
                "source_doc_hash": current_hash,
                "can_undo": len(active_state["undo_stack"]) > 0,
                "can_redo": len(active_state["redo_stack"]) > 0
            }), 409

        doc = active_state["working_document"]
        res = auto_fix_cad_document(
            doc=doc,
            target_margin_tics=target_margin,
            max_perturbation_m=max_perturbation,
            search_resolution_m=search_res,
            max_exact_jobs=6,
            route_id=route_id
        )

        if commit and res.get("success", False) and res.get("repaired_document") is not None:
            push_undo_state()
            active_state["working_document"] = CADDocument.from_dict(res["repaired_document"])

        res["source_doc_hash"] = compute_document_hash(active_state["working_document"])
        res["can_undo"] = len(active_state["undo_stack"]) > 0
        res["can_redo"] = len(active_state["redo_stack"]) > 0
        return jsonify(res), 200

    @app.route("/api/document/heatmap", methods=["GET", "POST"])
    def get_document_heatmap():
        """Compute live spatial heatmap and suffix Tactical Margin for active document (M2F).
        
        Optional request / query parameters:
        - route_id: Optional[str]
        - include_floor_grid: bool = False
        - grid_step_m: float = 0.25 (validated: 0.05 <= grid_step_m <= 5.0)
        - expected_doc_hash: Optional[str] (concurrency defense, returns 409 if stale)
        - client_revision: Optional[int] (echoed in response for client ordering)
        """
        req_data = (request.get_json(force=True, silent=True) if (request.is_json or request.method == "POST") else None) or {}
        route_id = req_data.get("route_id") or request.args.get("route_id")
        
        # Concurrency & provenance check
        expected_doc_hash = req_data.get("expected_doc_hash") or request.args.get("expected_doc_hash")
        client_rev = req_data.get("client_revision") or request.args.get("client_revision")
        if client_rev is not None:
            try:
                client_rev = int(client_rev)
            except (ValueError, TypeError):
                client_rev = None

        doc = active_state["working_document"]
        current_hash = compute_document_hash(doc)
        if expected_doc_hash and expected_doc_hash != current_hash:
            return jsonify({
                "is_valid": False,
                "error_code": "STALE_DOCUMENT_HASH",
                "error_reason": f"Expected document hash '{expected_doc_hash}' does not match active document hash '{current_hash}'.",
                "current_doc_hash": current_hash,
                "client_revision": client_rev
            }), 409

        # Grid resolution parsing and validation
        include_floor_grid = False
        if "include_floor_grid" in req_data:
            include_floor_grid = bool(req_data["include_floor_grid"])
        elif "include_floor_grid" in request.args:
            include_floor_grid = (request.args["include_floor_grid"].lower() == "true")

        raw_step = None
        if "grid_step_m" in req_data and req_data["grid_step_m"] is not None:
            raw_step = req_data["grid_step_m"]
        elif "grid_step_m" in request.args and request.args["grid_step_m"] is not None:
            raw_step = request.args["grid_step_m"]

        if raw_step is not None:
            try:
                grid_step_m = float(raw_step)
            except (ValueError, TypeError):
                return jsonify({
                    "is_valid": False,
                    "error_code": "INVALID_GRID_RESOLUTION",
                    "error_reason": f"Invalid non-numeric grid_step_m: '{raw_step}'"
                }), 422
        else:
            grid_step_m = 0.25

        import math
        if math.isnan(grid_step_m) or math.isinf(grid_step_m) or grid_step_m < 0.05 or grid_step_m > 5.0:
            return jsonify({
                "is_valid": False,
                "error_code": "INVALID_GRID_RESOLUTION",
                "error_reason": f"grid_step_m must be a finite number between 0.05m and 5.0m; got {grid_step_m}."
            }), 422

        route_heatmap = compute_cad_route_spatial_heatmap(
            doc=doc,
            route_id=route_id
        )

        if not route_heatmap.get("is_valid", False):
            return jsonify(route_heatmap), 422

        if client_rev is not None:
            route_heatmap["client_revision"] = client_rev

        if include_floor_grid:
            floor_data = compute_arena_floor_los_exposure(
                doc=doc,
                grid_step_m=grid_step_m
            )
            route_heatmap["floor_grid"] = floor_data
        else:
            route_heatmap["floor_grid"] = None

        return jsonify(route_heatmap), 200

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
