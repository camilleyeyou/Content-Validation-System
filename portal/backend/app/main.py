# portal/backend/app/main.py
"""
Content Portal API (FastAPI)
- Proper CORS for Vercel <-> Railway
- OAuth callback cookie fix (SameSite=None; Secure)
- Robust env normalization (no trailing slashes or hidden newlines)
- Debug endpoints for quick verification

Required env (Railway):
  PORTAL_BASE_URL=https://content-validation-system.vercel.app
  PORTAL_API_BASE=https://content-validation-system-production.up.railway.app
  LINKEDIN_REDIRECT_URI=https://content-validation-system-production.up.railway.app/auth/linkedin/callback
  LINKEDIN_CLIENT_ID=...
  LINKEDIN_CLIENT_SECRET=...
  LINKEDIN_VERSION=202509
  # Optional:
  # EXTRA_SCOPES="rw_organization_admin w_organization_social"
  # LINKEDIN_ORG_ID=123456789
  # CORS_ALLOW_ORIGINS="https://content-validation-system.vercel.app,https://your-preview.vercel.app"
  # CORS_ALLOW_ORIGIN_REGEX="^https://.*-content-validation-system.*\\.vercel\\.app$"
"""

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

# ------------------------------------------------------------------------------
# Ensure repo root on PYTHONPATH so we can import from src/
# ------------------------------------------------------------------------------
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ------------------------------------------------------------------------------
# LinkedIn service
# ------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# ------------------------------------------------------------------------------
# Env helpers / normalization
# ------------------------------------------------------------------------------
def _clean(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    # strip whitespace and newlines (avoids "%0A" in redirect URL)
    v = v.strip()
    # remove a single trailing slash on origins/bases
    if v.endswith("/") and ("http://" in v or "https://" in v):
        v = v[:-1]
    return v

PORTAL_BASE_URL = _clean(os.getenv("PORTAL_BASE_URL", "http://localhost:3000"))
PORTAL_API_BASE = _clean(os.getenv("PORTAL_API_BASE", "http://localhost:8001"))
REDIRECT_URI     = _clean(os.getenv("LINKEDIN_REDIRECT_URI", f"{PORTAL_API_BASE}/auth/linkedin/callback"))

LINKEDIN_CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LI_VERSION             = os.getenv("LINKEDIN_VERSION", "202509")

AUTH_URL  = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO  = "https://api.linkedin.com/v2/userinfo"
ORGS_ACLS = "https://api.linkedin.com/rest/organizationAcls"
ORGS_URL  = "https://api.linkedin.com/rest/organizations"

# ------------------------------------------------------------------------------
# Instantiate service
# ------------------------------------------------------------------------------
svc = LinkedInIntegrationService()

# ------------------------------------------------------------------------------
# Tiny in-memory store (MVP)
# ------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},     # sub -> {sub, name, email}
    "tokens": {},    # sub -> {access_token, version, updated_at}
    "posts": {},     # id  -> record sent to LI
    "approved": {}   # id  -> staged for manual publish
}

# ------------------------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="0.3.0")

# ----- CORS config -------------------------------------------------------------
def _compute_allowed_origins() -> List[str]:
    # Primary origin is your Vercel app
    origins = []
    if PORTAL_BASE_URL:
        origins.append(PORTAL_BASE_URL)

    # Extra allow-list (comma-separated) if you want previews, etc.
    extra = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if extra:
        for o in extra.split(","):
            o = _clean(o)
            if o and o not in origins:
                origins.append(o)

    # Local dev convenience
    if PORTAL_BASE_URL and "localhost" in PORTAL_BASE_URL:
        alt = PORTAL_BASE_URL.replace("localhost", "127.0.0.1")
        if alt not in origins:
            origins.append(alt)

    return origins

ALLOW_ORIGINS = _compute_allowed_origins()
ALLOW_ORIGIN_REGEX = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip() or None

# If you need regex (e.g., Vercel previews), set CORS_ALLOW_ORIGIN_REGEX.
# Otherwise, we use explicit allow_origins list.
if ALLOW_ORIGIN_REGEX:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=ALLOW_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS or ["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    )

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def want_org_scopes() -> bool:
    return bool(os.getenv("LINKEDIN_ORG_ID") or os.getenv("EXTRA_SCOPES"))

def scopes_for_auth(include_org: bool) -> str:
    scopes = ["openid", "profile", "email", "w_member_social"]
    if include_org:
        for s in ["rw_organization_admin", "w_organization_social"]:
            if s not in scopes:
                scopes.append(s)
    extra = (os.getenv("EXTRA_SCOPES") or "").strip().split()
    for s in extra:
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

def _is_secure_request(request: Request) -> bool:
    # Works behind Railway proxy
    xfproto = request.headers.get("x-forwarded-proto", "").lower()
    if xfproto == "https":
        return True
    return request.url.scheme == "https"

def set_token_for_service(access_token: str):
    os.environ["LINKEDIN_ACCESS_TOKEN"] = access_token
    try:
        svc.publisher.config.access_token = access_token
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

# ------------------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------------------
class ComposeIn(BaseModel):
    commentary: str
    hashtags: List[str] = []
    target: str = "AUTO"      # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = True

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"
    org_id: Optional[str] = None
    publish_now: bool = False

# ------------------------------------------------------------------------------
# Basic / Debug
# ------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI",
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
        "redirect_uri": REDIRECT_URI,
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
        "redirect_uri": REDIRECT_URI,
        "client_id_set": bool(LINKEDIN_CLIENT_ID),
        "scopes": scopes_for_auth(want_org_scopes()),
        "allow_origins": ALLOW_ORIGINS,
        "allow_origin_regex": ALLOW_ORIGIN_REGEX,
    }

@app.get("/debug/whoami")
def debug_whoami(request: Request):
    return {
        "cookie_li_sub_present": bool(request.cookies.get("li_sub")),
        "origin_header": request.headers.get("origin"),
        "x_forwarded_proto": request.headers.get("x-forwarded-proto"),
    }

# ------------------------------------------------------------------------------
# OAuth: login + callback
# ------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True):
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.head("/auth/linkedin/login")
def linkedin_login_head(include_org: bool = True):
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.get("/auth/linkedin/callback")
def linkedin_callback(request: Request, code: str, state: Optional[str] = None):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
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

    resp = RedirectResponse(url=f"{PORTAL_BASE_URL}/dashboard")
    # Cross-site cookie: must be SameSite=None; Secure on HTTPS
    secure = _is_secure_request(request)
    resp.set_cookie(
        "li_sub",
        sub,
        httponly=False,         # FE needs to read it? If not, set True.
        samesite="none" if secure else "lax",
        secure=secure,
        max_age=7 * 24 * 3600,
        path="/"
    )
    return resp

# ------------------------------------------------------------------------------
# Me / Orgs
# ------------------------------------------------------------------------------
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
    headers["X-RestLi-Method"] = "FINDER"

    # 1) org ACLs (what orgs does this member administer)
    # per LinkedIn REST spec, you filter by role & state & assignee
    params = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}"
    }
    acls = requests.get(ORGS_ACLS, headers=headers, params=params, timeout=20)
    if not acls.ok:
        return JSONResponse(status_code=acls.status_code, content={"error": acls.text})

    org_ids = []
    for el in acls.json().get("elements", []):
        urn = el.get("organization")
        if urn and urn.startswith("urn:li:organization:"):
            org_ids.append(urn.split(":")[-1])

    orgs = []
    # 2) get basic org info by id (optional)
    if org_ids:
        ids_param = ",".join(f"urn:li:organization:{oid}" for oid in org_ids)
        org_resp = requests.get(ORGS_URL, headers=headers, params={"ids": ids_param}, timeout=20)
        if org_resp.ok:
            data = org_resp.json()
            elements = data.get("elements") or []
            for o in elements:
                urn = o.get("id") or o.get("urn")
                org_id = str(o.get("id") or "").split(":")[-1] if isinstance(o.get("id"), str) else None
                # fallback: parse from urn if present
                if not org_id and isinstance(urn, str) and urn.startswith("urn:li:organization:"):
                    org_id = urn.split(":")[-1]
                orgs.append({
                    "id": org_id or "",
                    "name": (o.get("localizedName") or o.get("name") or ""),
                })
        else:
            # If that endpoint fails, return bare IDs
            orgs = [{"id": oid, "name": ""} for oid in org_ids]

    return {"orgs": orgs}

# ------------------------------------------------------------------------------
# Compose / Publish
# ------------------------------------------------------------------------------
class _ComposeResponse(BaseModel):
    id: str
    user_sub: str
    target_type: str
    target_urn: str
    commentary: str
    hashtags: List[str]
    lifecycle: str
    li_post_id: Optional[str]
    created_at: str

@app.post("/api/posts", response_model=_ComposeResponse)
async def create_post(payload: ComposeIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

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

# ------------------------------------------------------------------------------
# Pipeline: run and stage approved
# ------------------------------------------------------------------------------
def _import_run_full():
    """
    Robustly import the coroutine `test_complete_system` regardless of location.
    """
    try:
        from test_complete_system import test_complete_system as _run_full
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from tests_complete_system import test_complete_system as _run_full
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from tests.test_complete_system import test_complete_system as _run_full
        return _run_full
    except ModuleNotFoundError:
        pass
    try:
        from src.tests.test_complete_system import test_complete_system as _run_full
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
        "approved_samples": [r["id"] for r in saved[:5]],
    }

# ------------------------------------------------------------------------------
# Approved queue: list / publish / clear
# ------------------------------------------------------------------------------
@app.get("/api/approved")
def list_approved(user=Depends(get_user)):
    return [r for r in DB["approved"].values() if r["user_sub"] == user["sub"]]

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
