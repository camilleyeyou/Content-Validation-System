# portal/backend/app/main.py
from __future__ import annotations

import os
import json
import inspect
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

app = FastAPI()

# ----------------------------- CORS ---------------------------------
# Configure which frontends are allowed to call this API
CORS_ORIGINS = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "https://content-validation-system.vercel.app,http://localhost:3000",
)
allowed_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# --------------------------- Sessions --------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-me"),
    # SameSite/Lax works for OAuth redirect flows
)

# ------------------------ Settings storage ---------------------------
class LinkedInSettings(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str  # full https URL back to this API: /auth/linkedin/callback

SETTINGS_KEY = "LINKEDIN_SETTINGS_JSON"

def get_settings() -> Optional[LinkedInSettings]:
    raw = os.getenv(SETTINGS_KEY)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return LinkedInSettings(**data)
    except Exception:
        return None

def save_settings_to_env(s: LinkedInSettings) -> None:
    os.environ[SETTINGS_KEY] = json.dumps(s.model_dump())

# CORS preflight convenience (middleware already handles it, 200 is fine)
@app.options("/api/settings/linkedin")
def options_settings() -> PlainTextResponse:
    return PlainTextResponse("ok", status_code=200)

@app.get("/api/settings/linkedin")
def get_settings_endpoint() -> dict:
    return {"ok": True, "settings_present": bool(get_settings())}

@app.post("/api/settings/linkedin")
def set_settings_endpoint(payload: LinkedInSettings) -> dict:
    save_settings_to_env(payload)
    return {"ok": True}

# ------------------------------ OAuth --------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True):
    s = get_settings()
    if not s:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")

    scope = "openid profile email w_member_social rw_organization_admin w_organization_social"
    state = f"include_org:{1 if include_org else 0}"

    params = {
        "response_type": "code",
        "client_id": s.client_id,
        "redirect_uri": s.redirect_uri,  # must exactly match in LinkedIn app
        "scope": scope,
        "state": state,
    }
    url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return RedirectResponse(url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: str, request: Request):
    s = get_settings()
    if not s:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": str(s.redirect_uri),  # ensure plain str (avoid AnyHttpUrl issues)
        "client_id": s.client_id,
        "client_secret": s.client_secret,
    }
    r = requests.post(token_url, data=form, timeout=20)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {r.text}")

    tokens = r.json()  # access_token, refresh_token?, expires_in, etc.

    # Mark session as signed-in (extend with profile info as needed)
    request.session["li_auth"] = True
    request.session["li_access_token"] = tokens.get("access_token")

    # back to your UI (adjust if you want to go to a specific page)
    return RedirectResponse(url="/", status_code=307)

# --------------------- Batch runner (sync/async safe) ----------------
def _import_run_full() -> Callable[..., Any]:
    """
    Try to import your pipeline function. Return a callable that may be sync or async.
    """
    try:
        from src.pipeline.run_full import run_full as fn  # type: ignore
        return fn
    except Exception:
        pass

    try:
        # test harness fallback (often async)
        from test_complete_system import test_complete_system as fn  # type: ignore
        return fn
    except Exception as e:
        raise RuntimeError(f"Unable to import batch function: {e}")

@app.post("/api/run-batch")
async def run_batch():
    fn = _import_run_full()
    try:
        if inspect.iscoroutinefunction(fn):
            result = await fn()
        else:
            maybe = fn()
            if inspect.isawaitable(maybe):
                result = await maybe
            else:
                result = maybe
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"run-batch failed: {e}")

    payload: dict[str, Any] = {}
    if isinstance(result, dict):
        payload = result

    return JSONResponse({"ok": True, "approved_count": payload.get("approved_count")})

# ---------------------- Minimal API stubs for UI ---------------------
@app.get("/api/me")
def api_me(request: Request):
    if not request.session.get("li_auth"):
        raise HTTPException(status_code=401, detail="Not signed in")
    return {"sub": "me", "name": "LinkedIn User", "email": None, "org_preferred": None}

@app.get("/api/approved")
def api_approved(request: Request):
    if not request.session.get("li_auth"):
        # your UI handles 401; return 401 to hide items when not signed in
        raise HTTPException(status_code=401, detail="Not signed in")
    # TODO: replace with your real queue
    return []

@app.get("/api/orgs")
def api_orgs(request: Request):
    if not request.session.get("li_auth"):
        raise HTTPException(status_code=401, detail="Not signed in")
    # TODO: replace with real managed org IDs
    return {"orgs": []}

@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
    }
