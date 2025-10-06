# portal/backend/app/main.py
import os
import json
import time
import uuid
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from pathlib import Path
import sys

# --------------------------------------------------------------------------------------
# Ensure repo root is on PYTHONPATH so `src/` and root modules are importable
# --------------------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # .../Content-Validation-System
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --------------------------------------------------------------------------------------
# LinkedIn Publisher import
# --------------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# --------------------------------------------------------------------------------------
# Environment / Defaults
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")   # Next.js
PORTAL_API_BASE = os.getenv("PORTAL_API_BASE", "http://localhost:8001")   # FastAPI self
DEFAULT_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", f"{PORTAL_API_BASE}/auth/linkedin/callback")

LI_VERSION = os.getenv("LINKEDIN_VERSION", "202509")

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
ORGS_URL_REST = "https://api.linkedin.com/rest/organizationAcls"  # preferred
ORGS_URL_V2 = "https://api.linkedin.com/v2/organizationAcls"      # fallback

# --------------------------------------------------------------------------------------
# Instantiate integration service (reads env + token file if your code supports it)
# --------------------------------------------------------------------------------------
svc = LinkedInIntegrationService()

# --------------------------------------------------------------------------------------
# In-memory DB (simple for MVP). We can persist to file/DB later.
# --------------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},      # key = li_sub -> {sub, name, email}
    "tokens": {},     # key = li_sub -> {access_token, version, updated_at}
    "posts": {},      # key = internal id -> posts ledger
    "approved": {},   # key = internal id -> approved by pipeline, not yet sent
    "app_settings": {  # LinkedIn app settings stored via public endpoints
        "linkedin": {}
    },
}

# --------------------------------------------------------------------------------------
# Persisted settings file
# --------------------------------------------------------------------------------------
SETTINGS_FILE = Path("config/app_settings.json")
SETTINGS_FILE.parent.mkdir(exist_ok=True)

def _load_settings_from_disk() -> Dict[str, Any]:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save_settings_to_disk(data: Dict[str, Any]) -> None:
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))

def get_linkedin_settings() -> Dict[str, Any]:
    on_disk = _load_settings_from_disk() or {}
    li_disk = on_disk.get("linkedin") or {}
    li_mem = DB.get("app_settings", {}).get("linkedin") or {}
    # memory overrides nothing, just merge
    li = {**li_disk, **li_mem}
    return li

def set_linkedin_settings(newvals: Dict[str, Any]) -> Dict[str, Any]:
    all_settings = _load_settings_from_disk() or {}
    li = all_settings.get("linkedin") or {}
    # only update provided keys
    li.update({k: v for k, v in newvals.items() if v is not None})
    all_settings["linkedin"] = li
    _save_settings_to_disk(all_settings)
    DB["app_settings"]["linkedin"] = li

    # Mirror to environment for any code that reads env
    if "client_id" in li:
        os.environ["LINKEDIN_CLIENT_ID"] = li["client_id"]
    if "client_secret" in li:
        os.environ["LINKEDIN_CLIENT_SECRET"] = li["client_secret"]
    if "redirect_uri" in li:
        os.environ["LINKEDIN_REDIRECT_URI"] = li["redirect_uri"]
    if "version" in li:
        os.environ["LINKEDIN_VERSION"] = li["version"]
    if "org_id" in li:
        os.environ["LINKEDIN_ORG_ID"] = li["org_id"]

    # keep publisher config aligned
    try:
        svc.publisher.config.client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
        svc.publisher.config.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")
        svc.publisher.config.redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", DEFAULT_REDIRECT_URI)
        svc.publisher.config.organization_id = os.getenv("LINKEDIN_ORG_ID", None)
    except Exception:
        pass

    return li

# --------------------------------------------------------------------------------------
# FastAPI app + CORS
# --------------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="0.3.0")

origins = [PORTAL_BASE_URL]
if "localhost" in PORTAL_BASE_URL:
    origins.append(PORTAL_BASE_URL.replace("localhost", "127.0.0.1"))

# Always also allow the Vercel preview/prod domain if present via env
extra_cors = os.getenv("EXTRA_CORS_ORIGINS", "")
for o in extra_cors.split(","):
    o = o.strip()
    if o:
        origins.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def want_org_scopes() -> bool:
    s = get_linkedin_settings()
    if isinstance(s.get("include_org_scopes"), bool):
        return bool(s["include_org_scopes"])
    return bool(os.getenv("LINKEDIN_ORG_ID") or os.getenv("EXTRA_SCOPES"))

def scopes_for_auth(include_org: bool) -> str:
    scopes = ["openid", "profile", "email", "w_member_social"]
    if include_org:
        for s in ["rw_organization_admin", "w_organization_social"]:
            if s not in scopes:
                scopes.append(s)
    extra = (get_linkedin_settings().get("extra_scopes") or os.getenv("EXTRA_SCOPES") or "").strip().split()
    for s in extra:
        if s and s not in scopes:
            scopes.append(s)
    return " ".join(scopes)

def _effective_client_id() -> str:
    s = get_linkedin_settings()
    return (s.get("client_id") or os.getenv("LINKEDIN_CLIENT_ID", "")).strip()

def _effective_client_secret() -> str:
    s = get_linkedin_settings()
    return (s.get("client_secret") or os.getenv("LINKEDIN_CLIENT_SECRET", "")).strip()

def _effective_redirect_uri() -> str:
    s = get_linkedin_settings()
    return (s.get("redirect_uri") or os.getenv("LINKEDIN_REDIRECT_URI", DEFAULT_REDIRECT_URI)).strip()

def rest_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": LI_VERSION,
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

def get_user(request: Request) -> Dict[str, Any]:
    sub = request.cookies.get("li_sub")
    if not sub:
        raise HTTPException(401, "Not authenticated")
    user = DB["users"].get(sub)
    if not user:
        raise HTTPException(401, "User not found")
    return user

def set_token_for_service(access_token: str):
    os.environ["LINKEDIN_ACCESS_TOKEN"] = access_token
    try:
        svc.publisher.config.access_token = access_token
        Path("config").mkdir(exist_ok=True)
        with open("config/linkedin_token.json", "w") as f:
            json.dump({"access_token": access_token}, f)
    except Exception:
        pass

# ---- Robust importer for test_complete_system (Option B) ------------------------------
def _import_run_full():
    """
    Robustly import the coroutine `test_complete_system` regardless of location.
    """
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
    publish_now: bool = True  # if False, create draft (when supported)

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"            # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = False       # False = create DRAFTs

# --------------------------------------------------------------------------------------
# Basic routes
# --------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
        "portal_base_url": os.getenv("PORTAL_BASE_URL", PORTAL_BASE_URL),
        "api_base": os.getenv("PORTAL_API_BASE", PORTAL_API_BASE),
        "redirect_uri": _effective_redirect_uri(),
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "redirect_uri": _effective_redirect_uri(),
        "client_id": _effective_client_id(),
        "scopes": scopes_for_auth(want_org_scopes())
    }

# --------------------------------------------------------------------------------------
# Public LinkedIn settings endpoints (no auth required, optional admin key)
# --------------------------------------------------------------------------------------
@app.options("/api/settings/linkedin")
def options_settings_linkedin():
    return JSONResponse({"ok": True})

@app.get("/api/settings/linkedin")
def get_settings_linkedin():
    s = get_linkedin_settings() or {}
    masked = s.copy()
    if masked.get("client_secret"):
        masked["client_secret"] = "********"
    return {"linkedin": masked}

@app.post("/api/settings/linkedin")
def post_settings_linkedin(payload: Dict[str, Any]):
    """
    Accepts JSON like:
    {
      "client_id": "...",
      "client_secret": "...",
      "redirect_uri": "https://.../auth/linkedin/callback",
      "version": "202509",
      "org_id": "123456",
      "extra_scopes": "rw_organization_admin w_organization_social",
      "include_org_scopes": true,
      "admin_key": "optional if SETTINGS_ADMIN_KEY is set"
    }
    """
    admin_key = os.getenv("SETTINGS_ADMIN_KEY", "")
    if admin_key and payload.get("admin_key") != admin_key:
        raise HTTPException(401, "Unauthorized: invalid setup key")

    saved = set_linkedin_settings({
        "client_id": payload.get("client_id"),
        "client_secret": payload.get("client_secret"),
        "redirect_uri": payload.get("redirect_uri"),
        "version": payload.get("version"),
        "org_id": payload.get("org_id"),
        "extra_scopes": payload.get("extra_scopes"),
        "include_org_scopes": payload.get("include_org_scopes"),
    })
    out = saved.copy()
    if out.get("client_secret"):
        out["client_secret"] = "********"
    return {"saved": out}

# --------------------------------------------------------------------------------------
# OAuth: login + callback (use saved settings first)
# --------------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True):
    client_id = _effective_client_id()
    redirect_uri = _effective_redirect_uri()
    if not client_id or not redirect_uri:
        raise HTTPException(400, "LinkedIn client settings missing. Save them at /api/settings/linkedin first.")
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.head("/auth/linkedin/login")
def linkedin_login_head(include_org: bool = True):
    client_id = _effective_client_id()
    redirect_uri = _effective_redirect_uri()
    if not client_id or not redirect_uri:
        return JSONResponse(status_code=400, content={"error": "LinkedIn client settings missing"})
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: Optional[str] = None):
    client_id = _effective_client_id()
    client_secret = _effective_client_secret()
    redirect_uri = _effective_redirect_uri()
    if not client_id or not client_secret or not redirect_uri:
        return JSONResponse(status_code=400, content={"error": "LinkedIn client settings missing"})

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

    ui = requests.get(USERINFO, headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    if not ui.ok:
        return JSONResponse(status_code=ui.status_code, content={"error": ui.text})
    info = ui.json()
    sub = info["sub"]
    name = info.get("name") or f"{info.get('given_name','')} {info.get('family_name','')}".strip()
    email = info.get("email")

    DB["users"][sub] = {"sub": sub, "name": name, "email": email}
    DB["tokens"][sub] = {"access_token": access_token, "version": LI_VERSION, "updated_at": datetime.utcnow().isoformat()+"Z"}

    set_token_for_service(access_token)

    # Send the user back to the Vercel UI if configured
    portal_url = os.getenv("PORTAL_BASE_URL", PORTAL_BASE_URL)
    resp = RedirectResponse(url=f"{portal_url}/dashboard")
    # IMPORTANT: cross-site fetch needs SameSite=None; Secure
    resp.set_cookie("li_sub", sub, httponly=False, samesite="None", secure=True)
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
        "org_preferred": os.getenv("LINKEDIN_ORG_ID")
    }

@app.get("/api/orgs")
def list_orgs(user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    headers = rest_headers(token)

    # Try REST first (finder variants differ across tenants—try both shapes)
    def _rest_try(params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        h = headers.copy()
        h["X-RestLi-Method"] = "FINDER"
        r = requests.get(ORGS_URL_REST, headers=h, params=params, timeout=20)
        if r.ok:
            return r.json()
        # 400s vary; return None to try the other shape
        return None

    data = None
    # shape A (older docs)
    params_a = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}",
    }
    data = _rest_try(params_a)
    if data is None:
        # shape B (newer param key)
        params_b = {
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "state": "APPROVED",
            "roleAssignee": f"urn:li:person:{user['sub']}",
        }
        data = _rest_try(params_b)

    # fallback to v2 if REST could not be used
    if data is None:
        params_v2 = {
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "state": "APPROVED",
            "assignee": f"urn:li:person:{user['sub']}"
        }
        r2 = requests.get(ORGS_URL_V2, headers={"Authorization": f"Bearer {token}"}, params=params_v2, timeout=20)
        if not r2.ok:
            return JSONResponse(status_code=r2.status_code, content={"error": r2.text})
        data = r2.json()

    orgs = []
    for el in data.get("elements", []):
        urn = el.get("organization")
        if urn and urn.startswith("urn:li:organization:"):
            org_id = urn.split(":")[-1]
            orgs.append({"urn": urn, "id": org_id})
    return {"orgs": orgs}

# --------------------------------------------------------------------------------------
# Compose / Publish (immediate or draft)
# --------------------------------------------------------------------------------------
class ComposeIn(BaseModel):
    commentary: str
    hashtags: List[str] = []
    target: str = "AUTO"
    org_id: Optional[str] = None
    publish_now: bool = True

@app.post("/api/posts")
async def create_post(payload: ComposeIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    # Decide target
    default_org = os.getenv("LINKEDIN_ORG_ID")
    target_type = "MEMBER"
    target_urn = f"urn:li:person:{user['sub']}"

    try:
        if payload.target == "ORG" and (payload.org_id or default_org):
            org_id = payload.org_id or default_org
            try:
                res = await svc.publisher.create_company_draft_post(
                    content=payload.commentary,
                    hashtags=payload.hashtags,
                    organization_id=org_id,
                    publish_now=payload.publish_now
                )
            except TypeError:
                res = await svc.publisher.create_company_draft_post(
                    content=payload.commentary,
                    hashtags=payload.hashtags,
                    organization_id=org_id
                )
            target_type = "ORG"
            target_urn = f"urn:li:organization:{org_id}"
        else:
            try:
                res = await svc.publisher.create_draft_post(
                    content=payload.commentary,
                    hashtags=payload.hashtags,
                    publish_now=payload.publish_now
                )
            except TypeError:
                res = await svc.publisher.create_draft_post(
                    content=payload.commentary,
                    hashtags=payload.hashtags
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

    batch = await run_full()  # your test returns a Batch-like object
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
        "approved_samples": [r["id"] for r in saved[:5]],
    }

# --------------------------------------------------------------------------------------
# Approved queue: list, publish selected, clear
# --------------------------------------------------------------------------------------
@app.get("/api/approved")
def list_approved(user=Depends(get_user)):
    return [r for r in DB["approved"].values() if r["user_sub"] == user["sub"]]

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"
    org_id: Optional[str] = None
    publish_now: bool = False

@app.post("/api/approved/publish")
async def publish_approved(payload: PublishApprovedIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    results = []
    default_org = os.getenv("LINKEDIN_ORG_ID")

    async def publish_one(rec: Dict[str, Any]) -> Dict[str, Any]:
        commentary = rec["content"]
        hashtags = rec.get("hashtags", [])
        try:
            if payload.target == "ORG" and (payload.org_id or default_org):
                org_id = payload.org_id or default_org
                try:
                    res = await svc.publisher.create_company_draft_post(
                        content=commentary,
                        hashtags=hashtags,
                        organization_id=org_id,
                        publish_now=payload.publish_now
                    )
                except TypeError:
                    res = await svc.publisher.create_company_draft_post(
                        content=commentary,
                        hashtags=hashtags,
                        organization_id=org_id
                    )
                target_type = "ORG"
                target_urn = f"urn:li:organization:{org_id}"
            else:
                try:
                    res = await svc.publisher.create_draft_post(
                        content=commentary,
                        hashtags=hashtags,
                        publish_now=payload.publish_now
                    )
                except TypeError:
                    res = await svc.publisher.create_draft_post(
                        content=commentary,
                        hashtags=hashtags
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
