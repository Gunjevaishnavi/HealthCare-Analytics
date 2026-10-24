"""
Authentication and Access Restriction Module
---------------------------------------------
Ensures access restriction as mandated by project acceptance criteria.
Supports:
1. Session-based authentication for Web UI dashboard.
2. API Key authentication via 'X-API-Key' or 'Authorization: Bearer <key>' headers for REST APIs.
"""

from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from backend.config import Config


def is_authenticated_user() -> bool:
    """Checks if web user is logged in via session."""
    return session.get("authenticated", False)


def get_authenticated_api_key_role():
    """Validates API Key from HTTP headers."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header.split(" ", 1)[1].strip()

    if api_key and api_key in Config.VALID_API_KEYS:
        return Config.VALID_API_KEYS[api_key]
    return None


def require_auth(f):
    """
    Decorator for endpoints accessible either via Web session or REST API Key.
    If unauthorized: redirects to login for HTML requests, returns 401 JSON for API requests.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Check web session
        if is_authenticated_user():
            return f(*args, **kwargs)

        # 2. Check API key header
        api_role = get_authenticated_api_key_role()
        if api_role:
            request.api_role = api_role
            return f(*args, **kwargs)

        # Not authenticated: decide response based on requested content type / path
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Unauthorized Access",
                "message": "Valid API Key required via 'X-API-Key' header or session login.",
                "valid_demo_key": "health-demo-key-2026"
            }), 401
        
        return redirect(url_for("auth.login_view", next=request.path))

    return decorated_function


def require_api_key(f):
    """Decorator strictly enforcing REST API Key or active session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_authenticated_user():
            return f(*args, **kwargs)
        
        api_role = get_authenticated_api_key_role()
        if api_role:
            request.api_role = api_role
            return f(*args, **kwargs)

        return jsonify({
            "error": "Unauthorized Access",
            "message": "Access restricted. Provide header 'X-API-Key: health-demo-key-2026' or authenticate.",
            "authorized": False
        }), 401

    return decorated_function
