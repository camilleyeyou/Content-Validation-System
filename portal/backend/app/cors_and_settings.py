# portal/backend/app/cors_and_settings.py
import os
import secrets
from typing import Dict, Any, Optional

from fastapi import APIRouter, FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# In-memory per-session store for LinkedIn app settings
# (kept small & scoped to the user's session)
_SETTINGS_STORE: Dict[str, Dict[str, str]] = {}

# ----- Pydantic models for request/response -----

class LinkedInSettingsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None  # if omitted we'll compute on login


class LinkedInSettingsOut(BaseModel):
    client_id: Optional[str] = None
    # do not echo secret; just signal presence
    has_client_secret: bool = False
    redirect_uri_effective: Optional[str] = None
    source: str  # "session", "env", "mixed", "none"


# ----- Helpers -----

def _get_session_id(request: Request) -> str:
    """Ensure the request has a stable session id (using SessionMiddleware)."""
    sid = request.session.get("sid")
    if not sid:
        sid = secrets.token_urlsafe(24)
        request.session["sid"] = sid
    return sid


def _portal_base_from_env() -> Optional[str]:
    v = os.getenv("PORTAL_BASE_URL", "") or os.getenv("FRONTEND_BASE_URL", "")
    v = v.strip().rstrip("/")
    return v or None


def _effective_settings(request: Request) -> Dict[str, Any]:
    """
    Resolve settings with this precedence:
    1) Per-session overrides POSTed by the user
    2) Environment defaults: LINKEDIN_CLIENT_ID/SECRET/REDIRECT_URI
    """
    sid = _get_session_id(request)
    sess = _SETTINGS_STORE.get(sid, {})

    env_client_id = os.getenv("LINKEDIN_CLIENT_ID") or ""
    env_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET") or ""
    env_redirect = (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip()

    eff = {
        "client_id": sess.get("client_id") or env_client_id or "",
        "client_secret": sess.get("client_secret") or env_client_secret or "",
        "redirect_uri": (sess.get("redirect_uri") or env_redirect or "").rstrip("/"),
        "source": "none",
    }

    # Source label for debugging
    has_sess = any(bool(sess.get(k)) for k in ("client_id", "client_secret", "redirect_uri"))
    has_env = any(bool(x) for x in (env_client_id, env_client_secret, env_redirect))
    eff["source"] = "session" if has_sess and not has_env else "env" if has_env and not has_sess else "mixed" if has_sess and has_env else "none"

    return eff


def _compute_default_redirect(request: Request) -> str:
    """
    Build a redirect_uri from the current request (works behind Railway proxy).
    Example: https://<railway-host>/auth/linkedin/callback
    """
    # Prefer X-Forwarded headers set by proxies
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.url.netloc
    base = f"{proto}://{host}".rstrip("/")
    return f"{base}/auth/linkedin/callback"


# ----- Public configuration entrypoint -----

def configure_cors_and_settings(app: FastAPI) -> None:
    """
    Call this exactly once from main.py after creating FastAPI().
    It will:
      - install SessionMiddleware (if not already installed)
      - install one CORSMiddleware allowing your Vercel app + previews
      - register GET/POST /api/settings/linkedin
    """
    # 1) Sessions (for per-session settings)
    # If SessionMiddleware already added in your app, skip adding another.
    has_session = any(isinstance(m, SessionMiddleware) for m in app.user_middleware)
    if not has_session:
        secret = os.getenv("SESSION_SECRET", "") or secrets.token_urlsafe(32)
        app.add_middleware(SessionMiddleware, secret_key=secret, same_site="lax", https_only=True)

    # 2) CORS — single source of truth
    vercel_main = _portal_base_from_env() or "https://content-validation-system.vercel.app"
    allow_origins = list(filter(None, [
        vercel_main,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]))

    # Remove any prior CORSMiddleware you might have added; keep one.
    # (Starlette doesn't support removing; the safest approach is "add exactly once")
    has_cors = any(isinstance(m, CORSMiddleware) for m in app.user_middleware)
    if not has_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,                      # exact origins
            allow_origin_regex=r"^https://([a-z0-9-]+\.)*vercel\.app$",  # preview URLs
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
            allow_headers=["*"],
            max_age=600,
        )

    # 3) Router for settings (no auth required)
    r = APIRouter()

    @r.options("/api/settings/linkedin")
    async def _settings_preflight(_: Request) -> Response:
        # With CORSMiddleware this path will already be handled, but having
        # an OPTIONS route here is harmless and guarantees 200 instead of 400.
        return Response(status_code=200)

    @r.get("/api/settings/linkedin", response_model=LinkedInSettingsOut)
    async def get_settings(request: Request) -> LinkedInSettingsOut:
        eff = _effective_settings(request)
        # If no redirect_uri anywhere, compute a sensible default
        redirect = eff["redirect_uri"] or _compute_default_redirect(request)
        return LinkedInSettingsOut(
            client_id=eff["client_id"] or None,
            has_client_secret=bool(eff["client_secret"]),
            redirect_uri_effective=redirect,
            source=eff["source"],
        )

    @r.post("/api/settings/linkedin", response_model=LinkedInSettingsOut)
    async def save_settings(request: Request, body: LinkedInSettingsIn) -> LinkedInSettingsOut:
        sid = _get_session_id(request)
        store = _SETTINGS_STORE.setdefault(sid, {})
        store["client_id"] = body.client_id.strip()
        store["client_secret"] = body.client_secret.strip()
        if body.redirect_uri:
            store["redirect_uri"] = body.redirect_uri.strip().rstrip("/")

        eff = _effective_settings(request)
        redirect = eff["redirect_uri"] or _compute_default_redirect(request)
        return LinkedInSettingsOut(
            client_id=eff["client_id"] or None,
            has_client_secret=bool(eff["client_secret"]),
            redirect_uri_effective=redirect,
            source=eff["source"],
        )

    app.include_router(r)
