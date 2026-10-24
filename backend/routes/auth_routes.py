"""
Authentication Routes: Web Login & API Key Verification
-------------------------------------------------------
Enforces restricted access per project criteria.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from backend.config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_view():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        api_key_input = request.form.get("api_key", "").strip()

        # Check API key first if provided
        if api_key_input and api_key_input in Config.VALID_API_KEYS:
            session["authenticated"] = True
            session["username"] = f"KeyUser ({api_key_input[:8]}...)"
            session["role"] = Config.VALID_API_KEYS[api_key_input]
            next_url = request.args.get("next") or url_for("dashboard_view")
            return redirect(next_url)

        # Check credentials
        default_user = Config.DEFAULT_USER
        if username == default_user["username"] and password == default_user["password"]:
            session["authenticated"] = True
            session["username"] = default_user["username"]
            session["role"] = default_user["role"]
            next_url = request.args.get("next") or url_for("dashboard_view")
            return redirect(next_url)
        else:
            flash("Invalid credentials or API Key. Use default demo credentials provided below.", "danger")

    return render_template(
        "login.html",
        default_user=Config.DEFAULT_USER,
        demo_keys=Config.VALID_API_KEYS,
        disclaimer=Config.MANDATORY_LIMITATIONS_STATEMENT
    )


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout_view():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login_view"))


@auth_bp.route("/api/v1/auth/verify-key", methods=["POST"])
def verify_api_key():
    """Validates an API key payload."""
    data = request.get_json(silent=True) or {}
    api_key = data.get("api_key") or request.headers.get("X-API-Key")

    if api_key and api_key in Config.VALID_API_KEYS:
        return jsonify({
            "valid": True,
            "role": Config.VALID_API_KEYS[api_key],
            "message": "API Key is valid and authorized for educational healthcare analytics.",
            "limitations_notice": Config.MANDATORY_LIMITATIONS_STATEMENT
        }), 200

    return jsonify({
        "valid": False,
        "error": "Invalid or revoked API Key.",
        "provided_key": api_key
    }), 401
