# portal/backend/app/main.py
import os
import re
import time
import json
import secrets
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Query, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# =============================================================================
# App init
# =============================================================================
app = FastAPI(title="Content Portal API", version="1.0.0")

# Sessions (per-session app creds + oauth state)
if not any(isinstance(m, SessionMiddleware) for m in app.user_middleware):
    session_secret = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
    app.add_middleware(
        SessionMiddleware,
        secret_key=session_secret,
        same_site="lax",
        https_only=True,
    )

# =============================================================================
# CORS — flexible & env-driven
# =============================================================================
def _stripped_or_none(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    s = v.strip().rstrip("/")
    return s or None

def _portal_base_from_env() -> Optional[str]:
    return _stripped_or_none(os.getenv("PORTAL_BASE_URL") or os.getenv("FRONTEND_BASE_URL"))

def _csv_env(name: str) -> List[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    return [x.strip().rstrip("/") for x in raw.split(",") if x.strip()]

DEFAULT_PORTAL = "https://content-validation-system.vercel.app"

# Compute allow list
allow_all = os.getenv("CORS_ALLOW_ALL", "").strip() in ("1", "true", "TRUE", "yes", "on")

# Explicit origins from env (CSV)
env_origins = _csv_env("CORS_ALLOW_ORIGINS")

# Always consider the configured portal (or default)
portal_origin = _portal_base_from_env() or DEFAULT_PORTAL

# Local devs
local_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Final explicit list (dedup, keep order-ish)
seen = set()
explicit_allow = []
for o in [*env_origins, portal_origin, *local_origins]:
    if o and o not in seen:
        explicit_allow.append(o)
        seen.add(o)

# Regex (from env or default *.vercel.app + localhost)
allow_regex = os.getenv(
    "CORS_ALLOW_REGEX",
    r"^https://([a-z0-9-]+\.)*vercel\.app$|^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
)

# Install middleware
if not any(isinstance(m, CORSMiddleware) for m in app.user_middleware):
    app.add_middleware(
        CORSMiddleware,
        # If allow_all -> do not set wildcard '*' (Starlette rejects with allow_credentials=True)
        allow_origins=[] if allow_all else explicit_allow,
        allow_origin_regex=".*" if allow_all else allow_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        max_age=600,
    )

# =============================================================================
# In-memory stores per-session
# =============================================================================
_SETTINGS_STORE: Dict[str, Dict[str, str]] = {}
_TOKENS: Dict[str, Dict[str, Any]] = {}
_ME: Dict[str, Dict[str, Any]] = {}
_ORGS: Dict[str, List[Dict[str, str]]] = {}
_APPROVED: Dict[str, List[Dict[str, Any]]] = {}

# =============================================================================
# Models
# =============================================================================
class LinkedInSettingsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: Optional[str] = None

class LinkedInSettingsOut(BaseModel):
    client_id: Optional[str] = None
    has_client_secret: bool = False
    redirect_uri_effective: Optional[str] = None
    source: str  # "session" | "env" | "mixed" | "none"

class ApprovedPublishIn(BaseModel):
    ids: List[str]
    target: str            # "MEMBER" | "ORG"
    publish_now: bool = False
    org_id: Optional[str] = None

# =============================================================================
# Helpers
# =============================================================================
def _sid(request: Request) -> str:
    sid = request.session.get("sid")
    if not sid:
        sid = secrets.token_urlsafe(24)
        request.session["sid"] = sid
    return sid

def _compute_default_redirect(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.url.netloc
    return f"{proto}://{host}/auth/linkedin/callback"

def _effective_settings(request: Request) -> Dict[str, Any]:
    sid = _sid(request)
    sess = _SETTINGS_STORE.get(sid, {})

    env_client_id = os.getenv("LINKEDIN_CLIENT_ID") or ""
    env_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET") or ""
    env_redirect = (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip().rstrip("/")

    eff = {
        "client_id": sess.get("client_id") or env_client_id or "",
        "client_secret": sess.get("client_secret") or env_client_secret or "",
        "redirect_uri": sess.get("redirect_uri") or env_redirect or "",
        "source": "none",
    }

    has_sess = any(sess.get(k) for k in ("client_id", "client_secret", "redirect_uri"))
    has_env = any([env_client_id, env_client_secret, env_redirect])
    eff["source"] = "session" if (has_sess and not has_env) else \
                    "env"     if (has_env and not has_sess) else \
                    "mixed"   if (has_sess and has_env)     else "none"

    if not eff["redirect_uri"]:
        eff["redirect_uri"] = _compute_default_redirect(request)

    return eff

def _require_token(request: Request) -> Tuple[str, Dict[str, Any]]:
    sid = _sid(request)
    tok = _TOKENS.get(sid)
    if not tok or not tok.get("access_token"):
        raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn")
    return sid, tok

# =============================================================================
# Settings endpoints (per-session LinkedIn app creds)
# =============================================================================
settings_router = APIRouter()

@settings_router.options("/api/settings/linkedin")
async def settings_preflight(_: Request) -> Response:
    # CORS middleware handles headers; just return 200.
    return Response(status_code=200)

@settings_router.get("/api/settings/linkedin", response_model=LinkedInSettingsOut)
async def get_linkedin_settings(request: Request) -> LinkedInSettingsOut:
    eff = _effective_settings(request)
    return LinkedInSettingsOut(
        client_id=eff["client_id"] or None,
        has_client_secret=bool(eff["client_secret"]),
        redirect_uri_effective=eff["redirect_uri"],
        source=eff["source"],
    )

@settings_router.post("/api/settings/linkedin", response_model=LinkedInSettingsOut)
async def save_linkedin_settings(request: Request, body: LinkedInSettingsIn) -> LinkedInSettingsOut:
    sid = _sid(request)
    entry = _SETTINGS_STORE.setdefault(sid, {})
    entry["client_id"] = body.client_id.strip()
    entry["client_secret"] = body.client_secret.strip()
    if body.redirect_uri:
        entry["redirect_uri"] = body.redirect_uri.strip().rstrip("/")

    eff = _effective_settings(request)
    return LinkedInSettingsOut(
        client_id=eff["client_id"] or None,
        has_client_secret=bool(eff["client_secret"]),
        redirect_uri_effective=eff["redirect_uri"],
        source=eff["source"],
    )

app.include_router(settings_router)

# =============================================================================
# LinkedIn OAuth
# =============================================================================
LI_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LI_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LI_USERINFO = "https://api.linkedin.com/v2/userinfo"
ORG_SCOPES = ["rw_organization_admin", "w_organization_social"]
BASE_SCOPES = ["openid", "profile", "email", "w_member_social"]

@app.get("/auth/linkedin/login")
async def linkedin_login(request: Request, include_org: bool = Query(False)) -> Response:
    eff = _effective_settings(request)
    client_id = eff["client_id"]
    redirect_uri = eff["redirect_uri"]

    if not client_id:
        return JSONResponse({"error": "Missing LinkedIn client_id. Save it in settings first."}, status_code=400)

    state = str(int(time.time()))
    request.session["li_state"] = state
    # Remember where to send them back (if the frontend set it)
    back = request.query_params.get("back")
    if back:
        request.session["post_auth_redirect"] = back

    scopes = BASE_SCOPES + (ORG_SCOPES if include_org else [])
    scope_str = " ".join(scopes)

    # Properly encode params
    qp = httpx.QueryParams({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope_str,
        "state": state,
    })
    return RedirectResponse(f"{LI_AUTH_URL}?{qp}", status_code=307)

@app.get("/auth/linkedin/callback")
async def linkedin_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
) -> Response:
    if error:
        return JSONResponse({"error": error}, status_code=400)
    if not code or not state:
        return JSONResponse({"error": "Missing code/state"}, status_code=400)
    if request.session.get("li_state") != state:
        return JSONResponse({"error": "Invalid state"}, status_code=400)

    eff = _effective_settings(request)
    client_id = eff["client_id"]
    client_secret = eff["client_secret"]
    redirect_uri = eff["redirect_uri"]

    if not client_id or not client_secret:
        return JSONResponse({"error": "LinkedIn app credentials not configured."}, status_code=400)

    async with httpx.AsyncClient(timeout=30) as client:
        token_resp = await client.post(
            LI_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_resp.status_code != 200:
        return JSONResponse(
            {"error": "Token exchange failed", "detail": token_resp.text, "status": token_resp.status_code},
            status_code=400,
        )

    data = token_resp.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 0)
    if not access_token:
        return JSONResponse({"error": "No access_token in response"}, status_code=400)

    sid = _sid(request)
    _TOKENS[sid] = {
        "access_token": access_token,
        "expires_at": time.time() + int(expires_in or 0),
        "obtained_at": time.time(),
    }

    # Fetch userinfo for /api/me
    async with httpx.AsyncClient(timeout=30) as client:
        me_resp = await client.get(LI_USERINFO, headers={"Authorization": f"Bearer {access_token}"})
    if me_resp.status_code == 200:
        u = me_resp.json()
        _ME[sid] = {
            "sub": u.get("sub") or sid,
            "name": u.get("name") or u.get("given_name") or "LinkedIn User",
            "email": u.get("email"),
            "org_preferred": None,
        }
    else:
        _ME[sid] = {"sub": sid, "name": "LinkedIn User", "email": None, "org_preferred": None}

    portal = _portal_base_from_env() or DEFAULT_PORTAL
    to = request.session.get("post_auth_redirect") or f"{portal}/dashboard"
    return RedirectResponse(to, status_code=307)

# =============================================================================
# API routes
# =============================================================================
@app.get("/")
async def root(request: Request) -> Response:
    # Useful to quickly verify what CORS is configured to
    return JSONResponse(
        {
            "ok": True,
            "message": "Content Portal API – use /auth/linkedin/login or the UI",
            "portal_base_url": _portal_base_from_env() or DEFAULT_PORTAL,
            "api_base_hint": "http://localhost:8001",
            "redirect_uri_default": _compute_default_redirect(request),
            "cors": {
                "allow_all": allow_all,
                "allow_origins": explicit_allow,
                "allow_regex": allow_regex,
            },
        }
    )

@app.get("/api/me")
async def api_me(request: Request) -> Response:
    sid, _ = _require_token(request)
    return JSONResponse(_ME.get(sid) or {"sub": sid, "name": "LinkedIn User"})

@app.get("/api/orgs")
async def api_orgs(request: Request) -> Response:
    sid, tok = _require_token(request)
    at = tok["access_token"]

    if _ORGS.get(sid):
        return JSONResponse({"orgs": _ORGS[sid]})

    url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee&role=ADMINISTRATOR"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {at}"})
    if r.status_code == 403:
        return JSONResponse({"error": "Missing org scopes"}, status_code=403)
    if r.status_code != 200:
        return JSONResponse({"error": "LinkedIn org fetch failed", "detail": r.text}, status_code=400)

    data = r.json()
    orgs: List[Dict[str, str]] = []
    for el in data.get("elements", []):
        urn = el.get("organizationalTarget")
        if not urn:
            continue
        m = re.search(r"organization:(\d+)", urn)
        if not m:
            continue
        orgs.append({"id": m.group(1), "urn": urn})

    _ORGS[sid] = orgs
    return JSONResponse({"orgs": orgs})

@app.get("/api/approved")
async def api_approved(request: Request) -> Response:
    sid, _ = _require_token(request)
    queue = _APPROVED.setdefault(sid, [])
    queue_sorted = sorted(queue, key=lambda x: x.get("created_at", ""), reverse=True)
    return JSONResponse(queue_sorted)

@app.post("/api/approved/clear")
async def api_approved_clear(request: Request) -> Response:
    sid, _ = _require_token(request)
    deleted = len(_APPROVED.get(sid, []))
    _APPROVED[sid] = []
    return JSONResponse({"deleted": deleted})

async def _try_publish_to_linkedin(
    access_token: str,
    content: str,
    hashtags: List[str],
    target: str,
    org_id: Optional[str],
    publish_now: bool,
) -> Tuple[bool, Optional[str], Optional[str]]:
    author = "urn:li:person:me"
    if target == "ORG" and org_id:
        author = f"urn:li:organization:{org_id}"

    body = {
        "author": author,
        "commentary": content + (" " + " ".join(f"#{h.lstrip('#')}" for h in hashtags) if hashtags else ""),
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED" if publish_now else "DRAFT",
        "isReshareDisabledByAuthor": False,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post("https://api.linkedin.com/rest/posts", headers=headers, json=body)
        if r.status_code in (201, 202):
            data = r.json() if r.text else {}
            li_id = data.get("id") or data.get("entity") or "post-ok"
            return True, li_id, None
        else:
            try:
                err = r.json()
                err_msg = err.get("message") or r.text
            except Exception:
                err_msg = r.text
            return False, None, f"{r.status_code}: {err_msg}"
    except Exception as e:
        return False, None, str(e)

@app.post("/api/approved/publish")
async def api_approved_publish(request: Request, payload: ApprovedPublishIn) -> Response:
    sid, tok = _require_token(request)
    at = tok["access_token"]
    queue = _APPROVED.setdefault(sid, [])

    by_id = {p["id"]: p for p in queue}
    results = []
    successful = 0

    for pid in payload.ids:
        post = by_id.get(pid)
        if not post:
            results.append({"id": pid, "ok": False, "error": "Missing post"})
            continue

        ok, li_id, err = await _try_publish_to_linkedin(
            at,
            post.get("content", ""),
            post.get("hashtags", []),
            payload.target,
            payload.org_id,
            payload.publish_now,
        )
        if ok:
            successful += 1
            post["status"] = "published" if payload.publish_now else "draft"
            post["li_post_id"] = li_id
            post["error_message"] = None
        else:
            post["status"] = "error"
            post["error_message"] = err or "Unknown error"

        results.append({"id": pid, "ok": ok, "li_post_id": li_id, "error": err})

    return JSONResponse({"successful": successful, "results": results})

# =============================================================================
# /api/run-batch
# =============================================================================
def _import_run_full():
    import importlib.util
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[3]  # /app
    candidate = root / "test_complete_system.py"
    if candidate.exists():
        spec = importlib.util.spec_from_file_location("test_complete_system", str(candidate))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore
            if hasattr(mod, "run_full"):
                return getattr(mod, "run_full")

    async def _stub():
        return {
            "approved": [
                {
                    "id": secrets.token_hex(8),
                    "content": "Example approved post generated by fallback batch.",
                    "hashtags": ["ai", "python"],
                    "status": "approved",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
            ],
            "approved_count": 1,
            "batch_id": secrets.token_hex(6),
        }
    return _stub

@app.post("/api/run-batch")
async def run_batch(request: Request) -> Response:
    sid, _ = _require_token(request)
    run_full = _import_run_full()
    try:
        batch = await run_full()
    except Exception as e:
        return JSONResponse({"error": "run_full failed", "detail": str(e)}, status_code=500)

    approved_list = batch.get("approved") or []
    queue = _APPROVED.setdefault(sid, [])
    for item in approved_list:
        queue.append({
            "id": item.get("id") or secrets.token_hex(8),
            "content": item.get("content") or "",
            "hashtags": item.get("hashtags") or [],
            "status": item.get("status") or "approved",
            "created_at": item.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "li_post_id": item.get("li_post_id"),
            "error_message": item.get("error_message"),
            "user_sub": _ME.get(sid, {}).get("sub"),
        })

    return JSONResponse({"approved_count": len(approved_list), "batch_id": batch.get("batch_id")})
