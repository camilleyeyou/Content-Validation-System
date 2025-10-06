# portal/backend/app/main.py
from __future__ import annotations

import os
import json
import secrets
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, PlainTextResponse
from pydantic import BaseModel, ValidationError, AnyHttpUrl, TypeAdapter, field_validator
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

APP_NAME = "Content Portal API"
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_ACLS_URL = (
    "https://api.linkedin.com/v2/organizationalEntityAcls"
    "?q=roleAssignee&state=APPROVED&role=ADMINISTRATOR"
    "&projection=(elements*(organizationalTarget~(id,localizedName,vanityName)))"
)

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class LinkedInSettings(BaseModel):
    client_id: str
    client_secret: str
    # store as PLAIN STRING, but validate as URL
    redirect_uri: str
    scopes: Optional[List[str]] = None

    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, v: str) -> str:
        # Validate with AnyHttpUrl, but always return a plain string
        TypeAdapter(AnyHttpUrl).validate_python(v)
        return str(v)


class LinkedInSettingsPublic(BaseModel):
    client_id: str
    redirect_uri: str  # already validated, keep plain str
    scopes: Optional[List[str]] = None


class MeResponse(BaseModel):
    sub: str
    name: str
    email: Optional[str] = None
    org_preferred: Optional[str] = None


class ApprovedRec(BaseModel):
    id: str
    content: str
    hashtags: List[str] = []
    status: str
    created_at: str
    li_post_id: Optional[str] = None
    error_message: Optional[str] = None
    user_sub: Optional[str] = None


# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------

app = FastAPI(title=APP_NAME)

DEFAULT_ALLOWED_ORIGINS = [
    "https://content-validation-system.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", ",".join(DEFAULT_ALLOWED_ORIGINS)).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=True if os.getenv("FORCE_SESSION_SECURE", "1") == "1" else False,
)

# In-memory runtime LinkedIn settings (prime from env if present)
app.state.linkedin_settings: Optional[LinkedInSettings] = None

def _prime_linkedin_settings_from_env() -> None:
    cid = os.getenv("LI_CLIENT_ID")
    cs = os.getenv("LI_CLIENT_SECRET")
    ru = os.getenv("LI_REDIRECT_URI")
    scopes = os.getenv("LI_SCOPES")
    if cid and cs and ru:
        try:
            app.state.linkedin_settings = LinkedInSettings(
                client_id=cid,
                client_secret=cs,
                redirect_uri=ru,
                scopes=scopes.split() if scopes else None,
            )
        except ValidationError:
            # Ignore bad envs; UI can set them at runtime
            pass

_prime_linkedin_settings_from_env()

def _get_runtime_linkedin() -> LinkedInSettings:
    cfg = app.state.linkedin_settings
    if not cfg or not cfg.client_id or not cfg.client_secret or not cfg.redirect_uri:
        raise HTTPException(status_code=400, detail="LinkedIn settings are missing")
    return cfg

def _get_portal_base_url() -> str:
    return os.getenv("PORTAL_BASE_URL") or os.getenv("NEXT_PUBLIC_SITE_URL") or "http://localhost:3000"

def _get_api_base_url() -> str:
    return os.getenv("API_BASE_URL") or "http://localhost:8001"

# ------------------------------------------------------------------------------
# Root + tiny favicon
# ------------------------------------------------------------------------------

@app.get("/")
def root() -> Dict[str, Any]:
    cfg = app.state.linkedin_settings
    return {
        "ok": True,
        "message": f"{APP_NAME} – use /auth/linkedin/login or the UI",
        "portal_base_url": _get_portal_base_url(),
        "api_base": _get_api_base_url(),
        "redirect_uri": cfg.redirect_uri if cfg else None,
    }

@app.get("/favicon.ico")
def favicon():
    # simple tiny transparent icon
    return PlainTextResponse("", status_code=204)

# ------------------------------------------------------------------------------
# Runtime LinkedIn settings
# ------------------------------------------------------------------------------

@app.options("/api/settings/linkedin")
def options_settings() -> Response:
    return PlainTextResponse("ok", status_code=200)

@app.get("/api/settings/linkedin")
def get_settings() -> Dict[str, Any]:
    cfg = app.state.linkedin_settings
    if not cfg:
        return {"exists": False}
    pub = LinkedInSettingsPublic(
        client_id=cfg.client_id,
        redirect_uri=cfg.redirect_uri,
        scopes=cfg.scopes,
    )
    return {"exists": True, "settings": json.loads(pub.model_dump_json())}

@app.post("/api/settings/linkedin")
def set_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        cfg = LinkedInSettings(**payload)
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid settings: {ve}") from ve

    app.state.linkedin_settings = cfg
    pub = LinkedInSettingsPublic(
        client_id=cfg.client_id, redirect_uri=cfg.redirect_uri, scopes=cfg.scopes
    )
    return {"ok": True, "settings": json.loads(pub.model_dump_json())}

# ------------------------------------------------------------------------------
# LinkedIn OAuth
# ------------------------------------------------------------------------------

def _build_state(include_org: bool, sid: Optional[str]) -> str:
    parts = []
    if sid:
        parts.append(f"sid:{sid}")
    parts.append(f"include_org:{'1' if include_org else '0'}")
    return ":".join(parts)

def _parse_state(state: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    try:
        for part in state.split(":"):
            if not part:
                continue
            if part.startswith("sid"):
                _, val = part.split(":", 1)
                result["sid"] = val
            elif part.startswith("include_org"):
                _, val = part.split(":", 1)
                result["include_org"] = val
    except Exception:
        pass
    return result

@app.get("/auth/linkedin/login")
def linkedin_login(request: Request, include_org: bool = True, sid: Optional[str] = None):
    cfg = _get_runtime_linkedin()

    scopes = cfg.scopes or [
        "openid", "profile", "email",
        "w_member_social", "rw_organization_admin", "w_organization_social",
    ]

    params = {
        "response_type": "code",
        "client_id": str(cfg.client_id),
        "redirect_uri": str(cfg.redirect_uri),  # ensure plain string
        "scope": " ".join(scopes),
        "state": _build_state(include_org, sid),
    }
    url = f"{LINKEDIN_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url, status_code=307)

@app.get("/auth/linkedin/callback")
def linkedin_callback(request: Request, code: str, state: str):
    cfg = _get_runtime_linkedin()

    data = {
        "grant_type": "authorization_code",
        "code": str(code),
        "redirect_uri": str(cfg.redirect_uri),   # ensure plain string (fix)
        "client_id": str(cfg.client_id),
        "client_secret": str(cfg.client_secret),
    }

    try:
        r = requests.post(LINKEDIN_TOKEN_URL, data=data, timeout=20)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LinkedIn token request failed: {e}")

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"LinkedIn token error: {r.status_code} {r.text}")

    token_json = r.json()
    access_token = token_json.get("access_token")
    id_token = token_json.get("id_token")

    if not access_token:
        raise HTTPException(status_code=502, detail=f"LinkedIn token missing access_token: {token_json}")

    # Save to session
    request.session["li_access_token"] = str(access_token)
    request.session["li_id_token"] = str(id_token) if id_token else None

    parsed = _parse_state(state or "")
    request.session["include_org"] = parsed.get("include_org") == "1"
    if parsed.get("sid"):
        request.session["sid"] = parsed["sid"]

    return RedirectResponse(_get_portal_base_url(), status_code=307)

# ------------------------------------------------------------------------------
# Helpers for LinkedIn API calls
# ------------------------------------------------------------------------------

def _bearer_headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

def _get_access_token_from_session(request: Request) -> str:
    tok = request.session.get("li_access_token")
    if not tok:
        raise HTTPException(status_code=401, detail="Not signed in")
    return str(tok)

# ------------------------------------------------------------------------------
# API: Me, Orgs
# ------------------------------------------------------------------------------

@app.options("/api/me")
def options_me() -> Response:
    return PlainTextResponse("ok", status_code=200)

@app.get("/api/me")
def api_me(request: Request) -> MeResponse:
    access = _get_access_token_from_session(request)

    resp = requests.get(LINKEDIN_USERINFO_URL, headers=_bearer_headers(access), timeout=20)
    if resp.status_code == 200:
        u = resp.json()
        return MeResponse(
            sub=str(u.get("sub") or ""),
            name=u.get("name") or (f"{u.get('given_name','')} {u.get('family_name','')}".strip() or "LinkedIn User"),
            email=u.get("email"),
            org_preferred=request.session.get("org_preferred"),
        )

    me_r = requests.get("https://api.linkedin.com/v2/me", headers=_bearer_headers(access), timeout=20)
    if me_r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"LinkedIn /me failed: {me_r.status_code} {me_r.text}")

    me = me_r.json()
    name = (
        (me.get("localizedFirstName") or "")
        + (" " if me.get("localizedLastName") else "")
        + (me.get("localizedLastName") or "")
    ).strip() or "LinkedIn User"
    return MeResponse(sub=str(me.get("id") or ""), name=name, email=None, org_preferred=request.session.get("org_preferred"))

@app.options("/api/orgs")
def options_orgs() -> Response:
    return PlainTextResponse("ok", status_code=200)

@app.get("/api/orgs")
def api_orgs(request: Request) -> Dict[str, Any]:
    access = _get_access_token_from_session(request)
    r = requests.get(LINKEDIN_ACLS_URL, headers=_bearer_headers(access), timeout=20)
    if r.status_code == 403:
        return JSONResponse({"error": "missing_org_scopes"}, status_code=403)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"LinkedIn org ACLs failed: {r.status_code} {r.text}")

    data = r.json()
    orgs: List[Dict[str, str]] = []
    for el in data.get("elements", []):
        tgt = el.get("organizationalTarget~") or {}
        if "id" in tgt:
            orgs.append({
                "id": str(tgt.get("id")),
                "urn": f"urn:li:organization:{tgt.get('id')}",
            })
    return {"orgs": orgs}

# ------------------------------------------------------------------------------
# Approved content + Batch (fallback in-memory if your pipeline isn't present)
# ------------------------------------------------------------------------------

def _import_run_full():
    try:
        import importlib.util
        spec = importlib.util.find_spec("test_complete_system")
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return getattr(mod, "test_complete_system", None) or getattr(mod, "run_full", None)
    except Exception:
        pass
    return None

if not hasattr(app.state, "approved_store"):
    app.state.approved_store: List[ApprovedRec] = []

@app.options("/api/approved")
def options_approved() -> Response:
    return PlainTextResponse("ok", status_code=200)

@app.get("/api/approved")
def get_approved(request: Request) -> List[ApprovedRec]:
    return list(app.state.approved_store)

class PublishPayload(BaseModel):
    ids: List[str]
    target: str  # "MEMBER" | "ORG"
    publish_now: bool
    org_id: Optional[str] = None

@app.post("/api/approved/publish")
def publish_approved(request: Request, payload: PublishPayload) -> Dict[str, Any]:
    success = 0
    results = []
    for rec in app.state.approved_store:
        if rec.id in payload.ids:
            rec.status = "published"
            success += 1
            results.append({"id": rec.id, "ok": True})
    return {"successful": success, "results": results}

@app.post("/api/approved/clear")
def clear_approved(request: Request) -> Dict[str, Any]:
    n = len(app.state.approved_store)
    app.state.approved_store = []
    return {"deleted": n}

@app.options("/api/run-batch")
def options_run_batch() -> Response:
    return PlainTextResponse("ok", status_code=200)

@app.post("/api/run-batch")
async def run_batch(request: Request) -> Dict[str, Any]:
    # Require login
    _ = _get_access_token_from_session(request)

    run_full = _import_run_full()
    if run_full:
        try:
            result = run_full()
            if isinstance(result, dict):
                items = result.get("approved", [])
                for it in items:
                    try:
                        app.state.approved_store.append(ApprovedRec(**it))
                    except Exception:
                        pass
            return {"ok": True, "approved_count": len(app.state.approved_store)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Batch error: {e}")

    # Fallback: generate dummy items
    import datetime, uuid
    now = datetime.datetime.utcnow().isoformat() + "Z"
    new_items = [
        ApprovedRec(
            id=str(uuid.uuid4()),
            content="Sample approved post about product launch.",
            hashtags=["Launch", "Product", "Update"],
            status="approved",
            created_at=now,
        ),
        ApprovedRec(
            id=str(uuid.uuid4()),
            content="Another approved post with insights and tips.",
            hashtags=["Tips", "Insights"],
            status="approved",
            created_at=now,
        ),
        ApprovedRec(
            id=str(uuid.uuid4()),
            content="Approved content ready for scheduling.",
            hashtags=["Scheduling"],
            status="approved",
            created_at=now,
        ),
    ]
    app.state.approved_store.extend(new_items)
    return {"ok": True, "approved_count": len(new_items), "batch_id": secrets.token_hex(8)}

# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------

@app.get("/healthz")
def health() -> Dict[str, Any]:
    return {"ok": True}
