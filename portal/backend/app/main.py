# portal/backend/app/main.py
import os
import json
import time
import uuid
import urllib.parse
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

# --------------------------------------------------------------------------------------
# Ensure repo root is on PYTHONPATH so `src/` and root modules are importable
# --------------------------------------------------------------------------------------
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../Content-Validation-System
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --------------------------------------------------------------------------------------
# Load your LinkedIn integration service from the repo (used for posting)
# --------------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# --------------------------------------------------------------------------------------
# Environment / Config (fallbacks if no BYO config provided)
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")   # Next.js
PORTAL_API_BASE = os.getenv("PORTAL_API_BASE", "http://localhost:8001")   # FastAPI self
DEFAULT_REDIRECT_URI = os.getenv(
    "LINKEDIN_REDIRECT_URI",
    f"{PORTAL_API_BASE}/auth/linkedin/callback",
)

ENV_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
ENV_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
ENV_ORG_ID = os.getenv("LINKEDIN_ORG_ID", None)
LI_VERSION = os.getenv("LINKEDIN_VERSION", "202509")

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
ORGS_URL = "https://api.linkedin.com/rest/organizationAcls"  # X-RestLi-Method: FINDER

# --------------------------------------------------------------------------------------
# Instantiate integration service (publisher uses the user token we store below)
# --------------------------------------------------------------------------------------
svc = LinkedInIntegrationService()

# --------------------------------------------------------------------------------------
# In-memory DB (simple for MVP). You can persist to file/DB later.
# --------------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},        # key = li_sub -> {sub, name, email}
    "tokens": {},       # key = li_sub -> {access_token, version, updated_at}
    "posts": {},        # key = internal id -> posts ledger
    "approved": {},     # key = internal id -> approved-but-not-published
    "oauth_cfg": {},    # key = cfg(state) -> {client_id, client_secret, redirect_uri, org_id, created_at}
    "user_cfg": {},     # key = li_sub -> cfg (remember which config a user used)
}

# --------------------------------------------------------------------------------------
# FastAPI app + CORS
# --------------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="0.3.0")

origins = [PORTAL_BASE_URL]
if "localhost" in PORTAL_BASE_URL:
    origins.append(PORTAL_BASE_URL.replace("localhost", "127.0.0.1"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def want_org_scopes() -> bool:
    """Ask for org scopes if an org is configured or EXTRA_SCOPES is set."""
    return bool(ENV_ORG_ID or os.getenv("EXTRA_SCOPES"))

def scopes_for_auth(include_org: bool, extra_scopes: Optional[List[str]] = None) -> str:
    scopes = ["openid", "profile", "email", "w_member_social"]
    if include_org:
        for s in ["rw_organization_admin", "w_organization_social"]:
            if s not in scopes:
                scopes.append(s)
    extras = (extra_scopes or []) + (os.getenv("EXTRA_SCOPES", "").strip().split())
    for s in extras:
        s = s.strip()
        if s and s not in scopes:
            scopes.append(s)
    return " ".join(scopes)

def rest_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": LI_VERSION,
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

def set_token_for_service(access_token: str):
    """Expose token to the integration service and env. Persist token for CLI/tests."""
    os.environ["LINKEDIN_ACCESS_TOKEN"] = access_token
    try:
        svc.publisher.config.access_token = access_token  # align running service
        Path("config").mkdir(exist_ok=True)
        with open("config/linkedin_token.json", "w") as f:
            json.dump({"access_token": access_token}, f)
    except Exception:
        pass

def get_user(request: Request) -> Dict[str, Any]:
    sub = request.cookies.get("li_sub")
    if not sub:
        raise HTTPException(401, "Not authenticated")
    user = DB["users"].get(sub)
    if not user:
        raise HTTPException(401, "User not found")
    return user

def get_user_org_pref(sub: str) -> Optional[str]:
    """Prefer per-user Org ID (from BYO config) then env fallback."""
    cfg_key = DB["user_cfg"].get(sub)
    if cfg_key:
        org_id = DB["oauth_cfg"].get(cfg_key, {}).get("org_id")
        if org_id:
            return org_id
    return ENV_ORG_ID

# ---- Robust importer for test_complete_system (Option B) ------------------------------
def _import_run_full():
    """Robustly import the coroutine `test_complete_system` regardless of location."""
    try:
        from test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from tests_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from tests.test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from src.tests.test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass

    import importlib.util
    candidates = [
        REPO_ROOT / "test_complete_system.py",
        REPO_ROOT / "tests_complete_system.py",
        REPO_ROOT / "tests" / "test_complete_system.py",
        REPO_ROOT / "src" / "tests" / "test_complete_system.py",
    ]
    for p in candidates:
        if p.exists():
            spec = importlib.util.spec_from_file_location("test_complete_system", str(p))
            mod = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(mod)  # type: ignore
            return mod.test_complete_system  # type: ignore

    raise ModuleNotFoundError("Could not locate test_complete_system (root or tests/).")

# --------------------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------------------
class ComposeIn(BaseModel):
    commentary: str
    hashtags: List[str] = []
    target: str = "AUTO"      # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = True  # if False, create draft

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"            # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = False

class LinkedInConfigIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    org_id: Optional[str] = None
    include_org_scopes: bool = True
    extra_scopes: Optional[List[str]] = None

# --------------------------------------------------------------------------------------
# Basic routes
# --------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
        "redirect_uri": DEFAULT_REDIRECT_URI,
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "client_id_present": bool(ENV_CLIENT_ID),
        "scopes": scopes_for_auth(want_org_scopes()),
    }

# --------------------------------------------------------------------------------------
# NEW: Settings endpoints to store BYO LinkedIn app config
# --------------------------------------------------------------------------------------
@app.post("/api/settings/linkedin")
def save_linkedin_config(payload: LinkedInConfigIn, request: Request):
    """
    Save a user-provided LinkedIn app config and return a ready-to-use login URL.
    We generate a random `cfg` token and put it into the `state` param.
    """
    cfg = secrets.token_urlsafe(24)
    DB["oauth_cfg"][cfg] = {
        "client_id": payload.client_id.strip(),
        "client_secret": payload.client_secret.strip(),
        "redirect_uri": payload.redirect_uri.strip(),
        "org_id": (payload.org_id or "").strip() or None,
        "include_org_scopes": bool(payload.include_org_scopes),
        "extra_scopes": payload.extra_scopes or [],
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    params = {
        "response_type": "code",
        "client_id": DB["oauth_cfg"][cfg]["client_id"],
        "redirect_uri": DB["oauth_cfg"][cfg]["redirect_uri"],
        "scope": scopes_for_auth(DB["oauth_cfg"][cfg]["include_org_scopes"], DB["oauth_cfg"][cfg]["extra_scopes"]),
        "state": cfg,
    }
    return {
        "cfg": cfg,
        "login_url": f"{AUTH_URL}?{urllib.parse.urlencode(params)}",
    }

@app.get("/api/settings/linkedin")
def get_linkedin_config(user=Depends(get_user)):
    """Return a redacted view of the current user's active config."""
    cfg_key = DB["user_cfg"].get(user["sub"])
    if not cfg_key:
        return {"active": False}
    cfg = DB["oauth_cfg"].get(cfg_key)
    if not cfg:
        return {"active": False}
    redacted = {
        "active": True,
        "cfg": cfg_key,
        "client_id": cfg["client_id"][:4] + "..." + cfg["client_id"][-4:],
        "redirect_uri": cfg["redirect_uri"],
        "org_id": cfg.get("org_id"),
        "include_org_scopes": cfg.get("include_org_scopes", True),
        "extra_scopes": cfg.get("extra_scopes", []),
    }
    return redacted

# --------------------------------------------------------------------------------------
# OAuth: login + callback
# --------------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True, cfg: Optional[str] = None):
    """
    If `cfg` is provided, use that stored BYO config.
    Otherwise, fall back to environment variables.
    """
    if cfg and cfg in DB["oauth_cfg"]:
        cfg_obj = DB["oauth_cfg"][cfg]
        params = {
            "response_type": "code",
            "client_id": cfg_obj["client_id"],
            "redirect_uri": cfg_obj["redirect_uri"],
            "scope": scopes_for_auth(cfg_obj.get("include_org_scopes", True), cfg_obj.get("extra_scopes", [])),
            "state": cfg,
        }
        return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

    # Fallback: env-driven login (legacy)
    params = {
        "response_type": "code",
        "client_id": ENV_CLIENT_ID,
        "redirect_uri": DEFAULT_REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time())),
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

# Optional HEAD so `curl -I` doesn't 405
@app.head("/auth/linkedin/login")
def linkedin_login_head(include_org: bool = True, cfg: Optional[str] = None):
    return linkedin_login(include_org=include_org, cfg=cfg)

@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: Optional[str] = None):
    """
    Use `state` as our config key if present; otherwise fall back to env config.
    """
    use_env = True
    client_id = ENV_CLIENT_ID
    client_secret = ENV_CLIENT_SECRET
    redirect_uri = DEFAULT_REDIRECT_URI
    org_id = ENV_ORG_ID

    if state and state in DB["oauth_cfg"]:
        use_env = False
        c = DB["oauth_cfg"][state]
        client_id = c["client_id"]
        client_secret = c["client_secret"]
        redirect_uri = c["redirect_uri"]
        org_id = c.get("org_id")

    # Exchange code for access token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    tok = requests.post(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    if not tok.ok:
        return JSONResponse(status_code=tok.status_code, content={"error": tok.text})

    access_token = tok.json()["access_token"]

    # Verify identity (OIDC)
    ui = requests.get(USERINFO, headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    if not ui.ok:
        return JSONResponse(status_code=ui.status_code, content={"error": ui.text})
    info = ui.json()
    sub = info["sub"]
    name = info.get("name") or f"{info.get('given_name','')} {info.get('family_name','')}".strip()
    email = info.get("email")

    # Save session user + token in memory
    DB["users"][sub] = {"sub": sub, "name": name, "email": email}
    DB["tokens"][sub] = {"access_token": access_token, "version": LI_VERSION, "updated_at": datetime.utcnow().isoformat()+"Z"}

    # Remember which config this user authenticated with (if any)
    if not use_env and state:
        DB["user_cfg"][sub] = state

    # Expose token to service + persist to file used by CLI/tests
    set_token_for_service(access_token)

    # Set a readable cookie for the FE session (demo scope)
    resp = RedirectResponse(url=f"{PORTAL_BASE_URL}/dashboard")
    resp.set_cookie("li_sub", sub, httponly=False, samesite="Lax")
    return resp

# --------------------------------------------------------------------------------------
# Me / Orgs
# --------------------------------------------------------------------------------------
@app.get("/api/me")
def me(user=Depends(get_user)):
    return {
        "sub": user["sub"],
        "name": user["name"],
        "email": user.get("email"),
        "org_preferred": get_user_org_pref(user["sub"]),
    }

@app.get("/api/orgs")
def list_orgs(user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    headers = rest_headers(token)
    headers["X-RestLi-Method"] = "FINDER"

    # LinkedIn Organization ACLs query:
    params = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}",
    }
    r = requests.get(ORGS_URL, headers=headers, params=params, timeout=20)
    if not r.ok:
        return JSONResponse(status_code=r.status_code, content={"error": r.text})
    data = r.json()
    orgs = []
    for el in data.get("elements", []):
        urn = el.get("organization")
        if urn and urn.startswith("urn:li:organization:"):
            org_id = urn.split(":")[-1]
            orgs.append({"urn": urn, "id": org_id})
    return {"orgs": orgs}

# --------------------------------------------------------------------------------------
# Compose / Publish
# --------------------------------------------------------------------------------------
@app.post("/api/posts")
async def create_post(payload: ComposeIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    # Decide target (prefer per-user org config)
    user_org = get_user_org_pref(user["sub"])
    target_type = "MEMBER"
    target_urn = f"urn:li:person:{user['sub']}"

    try:
        if payload.target == "ORG" and (payload.org_id or user_org):
            org_id = payload.org_id or user_org
            res = await svc.publisher.create_company_draft_post(
                content=payload.commentary,
                hashtags=payload.hashtags,
                organization_id=org_id,
                publish_now=payload.publish_now
            )
            target_type = "ORG"
            target_urn = f"urn:li:organization:{org_id}"
        else:
            res = await svc.publisher.create_draft_post(
                content=payload.commentary,
                hashtags=payload.hashtags,
                publish_now=payload.publish_now
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    li_id = res.get("id") if isinstance(res, dict) else None
    rec = {
        "id": str(uuid.uuid4()),
        "user_sub": user["sub"],
        "target_type": target_type,
        "target_urn": target_urn,
        "commentary": payload.commentary,
        "hashtags": payload.hashtags,
        "lifecycle": "PUBLISHED" if payload.publish_now else "DRAFT",
        "li_post_id": li_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    DB["posts"][rec["id"]] = rec
    return rec

@app.get("/api/posts")
def list_posts(user=Depends(get_user)):
    return [p for p in DB["posts"].values() if p["user_sub"] == user["sub"]]

# --------------------------------------------------------------------------------------
# Run pipeline: store approved (no auto publish)
# --------------------------------------------------------------------------------------
@app.post("/api/run-batch")
async def run_batch(user=Depends(get_user), publish: bool = False):
    run_full = _import_run_full()

    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    batch = await run_full()
    approved = batch.get_approved_posts() if batch else []
    saved = []

    for p in approved:
        ap_id = str(uuid.uuid4())
        hashtags = []
        if hasattr(p, "hashtags") and p.hashtags:
            hashtags = p.hashtags
        elif getattr(p, "metadata", None):
            hashtags = p.metadata.get("hashtags", []) or []

        record = {
            "id": ap_id,
            "user_sub": user["sub"],
            "batch_id": getattr(batch, "id", None),
            "content": getattr(p, "content", str(p)),
            "hashtags": hashtags,
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "li_post_id": None,
            "error_message": None,
        }
        DB["approved"][ap_id] = record
        saved.append(record)

    return {
        "batch_id": getattr(batch, "id", None),
        "approved_count": len(saved),
        "approved_samples": [r["id"] for r in saved[:20]],  # show more ids
    }

# --------------------------------------------------------------------------------------
# Approved queue: list, publish selected, clear
# --------------------------------------------------------------------------------------
@app.get("/api/approved")
def list_approved(user=Depends(get_user)):
    # return ALL approved for the user (not only a slice)
    return [r for r in DB["approved"].values() if r["user_sub"] == user["sub"]]

@app.post("/api/approved/publish")
async def publish_approved(payload: PublishApprovedIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    results = []
    user_org = get_user_org_pref(user["sub"])

    async def publish_one(rec: Dict[str, Any]) -> Dict[str, Any]:
        commentary = rec["content"]
        hashtags = rec.get("hashtags", [])
        try:
            if payload.target == "ORG" and (payload.org_id or user_org):
                org_id = payload.org_id or user_org
                res = await svc.publisher.create_company_draft_post(
                    content=commentary,
                    hashtags=hashtags,
                    organization_id=org_id,
                    publish_now=payload.publish_now
                )
                target_type = "ORG"
                target_urn = f"urn:li:organization:{org_id}"
            else:
                res = await svc.publisher.create_draft_post(
                    content=commentary,
                    hashtags=hashtags,
                    publish_now=payload.publish_now
                )
                target_type = "MEMBER"
                target_urn = f"urn:li:person:{user['sub']}"

            li_id = res.get("id") if isinstance(res, dict) else None
            rec["status"] = "PUBLISHED" if payload.publish_now else "DRAFT_CREATED"
            rec["li_post_id"] = li_id
            rec["error_message"] = None

            DB["posts"][rec["id"]] = {
                "id": rec["id"],
                "user_sub": user["sub"],
                "target_type": target_type,
                "target_urn": target_urn,
                "commentary": commentary,
                "hashtags": hashtags,
                "lifecycle": "PUBLISHED" if payload.publish_now else "DRAFT",
                "li_post_id": li_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            return {"id": rec["id"], "success": True, "li_post_id": li_id}

        except Exception as e:
            rec["error_message"] = str(e)
            return {"id": rec["id"], "success": False, "error": str(e)}

    for ap_id in payload.ids:
        rec = DB["approved"].get(ap_id)
        if not rec or rec["user_sub"] != user["sub"]:
            results.append({"id": ap_id, "success": False, "error": "not found"})
            continue
        results.append(await publish_one(rec))

    ok = sum(1 for r in results if r["success"])
    return {"requested": len(payload.ids), "successful": ok, "results": results}

@app.post("/api/approved/clear")
def clear_approved(user=Depends(get_user)):
    to_delete = [k for k, v in DB["approved"].items() if v["user_sub"] == user["sub"]]
    for k in to_delete:
        del DB["approved"][k]
    return {"deleted": len(to_delete)}
