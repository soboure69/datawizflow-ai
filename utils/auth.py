from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st


def _auth_enabled() -> bool:
    default = "1" if os.environ.get("APP_ENV", "development").lower() == "production" else "0"
    return os.environ.get("APP_AUTH_ENABLED", default).strip().lower() in {"1", "true", "yes"}


def _verify_password(password: str, encoded: str) -> bool:
    """Verify PBKDF2-SHA256$iterations$salt$hex_digest from environment."""
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
        return hmac.compare_digest(candidate, expected)
    except (TypeError, ValueError):
        return False


def require_authentication() -> None:
    """Gate every page; production defaults to authenticated access."""
    if not _auth_enabled():
        return
    username = os.environ.get("APP_AUTH_USERNAME", "").strip()
    password_hash = os.environ.get("APP_AUTH_PASSWORD_HASH", "").strip()
    if not username or not password_hash:
        st.error("Authentication is required but not configured. Set APP_AUTH_USERNAME and APP_AUTH_PASSWORD_HASH.")
        st.stop()
    if st.session_state.get("authenticated_user"):
        return
    st.title("DataWizFlow AI")
    with st.form("login"):
        supplied_user = st.text_input("Username")
        supplied_password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        valid_user = hmac.compare_digest(supplied_user, username)
        if valid_user and _verify_password(supplied_password, password_hash):
            st.session_state["authenticated_user"] = username
            st.rerun()
        st.error("Invalid credentials.")
    st.stop()
