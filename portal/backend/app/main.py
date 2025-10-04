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

# --------------------------------------------------------------------------------------
# Ensure repo root is on PYTHONPATH so `src/` and root files are importable
# --------------------------------------------------------------------------------------
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../Content-Validation-System
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --------------------------------------------------------------------------------------
# LinkedIn integration service (uses your existing code)
# --------------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# --------------------------------------------------------------------------------------
# Environment / Config
# IMPORTANT: These values must match how you actually deploy.
# In Railway, set PORTAL_BASE_URL to your Vercel URL and LINKEDIN_REDIRECT_URI to
#   https://<railway-domain>/auth/linkedin/callback
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = (os.getenv("PORTAL_BASE_URL", "http://localhost:3000")).strip()
PORTAL_API_BASE = (os.getenv("PORTAL_API_BASE", "http://localhost:8001")).strip()
REDIRECT_URI = (os.getenv("LINKEDIN_REDIRECT_URI", f"{PORTAL_API_BASE}/auth/linkedin/callback")).strip()

LINKEDIN_CLIENT_ID = (os.getenv("LINKEDIN_CLIENT_ID", "")).strip()
LINKEDIN_CLIENT_SECRET = (os.getenv("LINKEDIN_CLIENT_SECRET", "")).strip()
LI_VERSION = (os.getenv("LINKEDIN_VERSION", "202509")).strip()

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_V2 = "https://api.linkedin.com/v2/userinfo"

# Orgs: try v2 first; if it fails, fallback to REST
ORGS_URL_V2 = "https://api.linkedin.com/v2/organizationAcls"
ORGS_URL_REST = "https://api.linkedin.com/rest/organizationAcls"

# --------------------------------------------------------------------------------------
# Instantiate integration service (reads env + token file if supported in your code)
# --------------------------------------------------------------------------------------
svc = LinkedInIntegrationService()

# --------------------------------------------------------------------------------------
# In-memory DB (MVP)
# --------------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},     # key = li_sub -> {sub, name, email}
    "tokens": {},    # key = li_sub -> {access_token, version, updated_at}
    "posts": {},     # key = internal id -> posted/draft ledger
    "approved": {}   # key = internal id -> approved for manual publishing
}

# --------------------------------------------------------------------------------------
# FastAPI app + CORS
# --------------------------------------------------------------------------------------
app = FastAPI(title="Content Portal API", version="0.3.0")

# CORS: allow multiple origins via env
origins_env = os.getenv("CORS_ALLOW_ORIGINS", PORTAL_BASE_URL)
origins = [o.strip() for o in origins_env.split(",") if o.strip()]
# convenience: if localhost present, also add 127.0.0.1 variant
extra_local = []
for o in origins:
    if "localhost" in o:
        extra_local.append(o.replace("localhost", "127.0.0.1"))
origins += extra_local

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # IMPORTANT for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def want_org_scopes() -> bool:
    """Ask for org scopes if an org is configured or EXTRA_SCOPES is set."""
    return bool(os.getenv("LINKEDIN_ORG_ID") or os.getenv("EXTRA_SCOPES"))

def scopes_for_auth(include_org: bool) -> str:
    scopes = ["openid", "profile", "email", "w_member_social"]
    if include_org:
        for s in ["rw_organization_admin", "w_organization_social"]:
            if s not in scopes:
                scopes.append(s)
    extra = (os.getenv("EXTRA_SCOPES") or "").strip().split()
    for s in extra:
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

def get_user(request: Request) -> Dict[str, Any]:
    sub = request.cookies.get("li_sub")
    if not sub:
        raise HTTPException(401, "Not authenticated")
    user = DB["users"].get(sub)
    if not user:
        raise HTTPException(401, "User not found")
    # sanity: also ensure token is present
    if sub not in DB["tokens"] or not DB["tokens"][sub].get("access_token"):
        raise HTTPException(401, "Session expired or token missing")
    return user

def set_token_for_service(access_token: str):
    """Expose token to the integration service and env. Persist to shared file for CLI/tests."""
    os.environ["LINKEDIN_ACCESS_TOKEN"] = access_token
    try:
        svc.publisher.config.access_token = access_token  # align running service
        # Persist the token so CLI/tools can reuse
        Path("config").mkdir(exist_ok=True)
        with open("config/linkedin_token.json", "w") as f:
            json.dump({"access_token": access_token}, f)
    except Exception:
        pass

def set_session_cookie(resp: RedirectResponse, sub: str):
    """
    Set cookie with correct flags:
      - In production (HTTPS frontend): SameSite=None; Secure
      - Local dev: SameSite=Lax; not Secure
    """
    secure = PORTAL_BASE_URL.startswith("https://")
    resp.set_cookie(
        key="li_sub",
        value=sub,
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/",
        httponly=True,
        samesite="none" if secure else "lax",
        secure=secure,
    )

# ---- Robust importer for test_complete_system (Option B) ------------------------------
def _import_run_full():
    """
    Robustly import the coroutine `test_complete_system` regardless of location.
    Tries root file, alt name, tests package, src/tests, then direct file path.
    """
    # 1) common root filename
    try:
        from test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass

    # 2) alt root name (if someone used tests_complete_system.py)
    try:
        from tests_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass

    # 3) in tests/ package
    try:
        from tests.test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass

    # 4) under src/tests (fallback)
    try:
        from src.tests.test_complete_system import test_complete_system as _run_full  # type: ignore
        return _run_full
    except ModuleNotFoundError:
        pass

    # 5) last resort: load by file path
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
            mod = importlib.util.module_from_spec(spec)  # type: ignore
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
    publish_now: bool = True  # if False, keep as a local draft

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"            # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = False       # False = create DRAFTs (or local drafts)

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
        "redirect_uri": REDIRECT_URI,
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "redirect_uri": REDIRECT_URI,
        "client_id_present": bool(LINKEDIN_CLIENT_ID),
        "scopes": scopes_for_auth(want_org_scopes()),
        "cors_allow_origins": origins,
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
    }

@app.get("/debug/whoami")
def whoami(request: Request):
    return {
        "cookie_li_sub_present": ("li_sub" in request.cookies),
        "cookie_li_sub_value_preview": (request.cookies.get("li_sub")[:6] + "…") if request.cookies.get("li_sub") else None,
        "users_cached": list(DB["users"].keys()),
        "tokens_cached": list(DB["tokens"].keys()),
    }

# --------------------------------------------------------------------------------------
# OAuth: login + callback
# --------------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True):
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(500, "LINKEDIN_CLIENT_ID is not configured on the server")

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    # Make sure no double slashes end up in the URL; LinkedIn is fine with this,
    # but your frontend must not call //auth/... (use absolute API_BASE)
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

# Optional: HEAD so `curl -I` shows redirect instead of 405
@app.head("/auth/linkedin/login")
def linkedin_login_head(include_org: bool = True):
    if not LINKEDIN_CLIENT_ID:
        raise HTTPException(500, "LINKEDIN_CLIENT_ID is not configured on the server")

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

@app.get("/auth/linkedin/callback")
def linkedin_callback(code: str, state: Optional[str] = None):
    # Exchange code for access token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,  # MUST match the one used in /login and LinkedIn app settings
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

    access_token = tok.json().get("access_token")
    if not access_token:
        return JSONResponse(status_code=500, content={"error": "No access_token in LinkedIn response"})

    # Verify identity (OIDC v2)
    ui = requests.get(USERINFO_V2, headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    if not ui.ok:
        return JSONResponse(status_code=ui.status_code, content={"error": ui.text})
    info = ui.json()
    sub = info["sub"]
    name = info.get("name") or f"{info.get('given_name','')} {info.get('family_name','')}".strip()
    email = info.get("email")

    # Save session user + token in memory
    DB["users"][sub] = {"sub": sub, "name": name, "email": email}
    DB["tokens"][sub] = {"access_token": access_token, "version": LI_VERSION, "updated_at": datetime.utcnow().isoformat()+"Z"}

    # Expose token to service + persist to file used by CLI/tests
    set_token_for_service(access_token)

    # Redirect to the dashboard on the frontend (ensure cookie is sent cross-site)
    resp = RedirectResponse(url=f"{PORTAL_BASE_URL}/dashboard", status_code=303)
    set_session_cookie(resp, sub)
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

    # Try v2 first
    params = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}"
    }
    h_v2 = rest_headers(token)
    r = requests.get(ORGS_URL_V2, headers=h_v2, params=params, timeout=20)
    if not r.ok:
        # fallback to REST endpoint (with FINDER header)
        h_rest = rest_headers(token)
        h_rest["X-RestLi-Method"] = "FINDER"
        r2 = requests.get(ORGS_URL_REST, headers=h_rest, params=params, timeout=20)
        if not r2.ok:
            return JSONResponse(status_code=r2.status_code, content={"error": r2.text})
        data = r2.json()
    else:
        data = r.json()

    orgs = []
    for el in data.get("elements", []):
        urn = el.get("organization")
        if urn and urn.startswith("urn:li:organization:"):
            org_id = urn.split(":")[-1]
            orgs.append({"urn": urn, "id": org_id})
    return {"orgs": orgs}

# --------------------------------------------------------------------------------------
# Compose / Publish (immediate or local draft)
# --------------------------------------------------------------------------------------
class ComposeIn(BaseModel):
    commentary: str
    hashtags: List[str] = []
    target: str = "AUTO"      # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = True  # else local draft

@app.post("/api/posts")
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
        "lifecycle": "PUBLISHED" if payload.publish_now else "LOCAL_DRAFT",
        "li_post_id": li_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    DB["posts"][rec["id"]] = rec
    return rec

@app.get("/api/posts")
def list_posts(user=Depends(get_user)):
    return [p for p in DB["posts"].values() if p["user_sub"] == user["sub"]]

# --------------------------------------------------------------------------------------
# Run pipeline: store approved (manual publish later)
# --------------------------------------------------------------------------------------
@app.post("/api/run-batch")
async def run_batch(user=Depends(get_user), publish: bool = False):
    """
    Runs your generation/validation pipeline and stores approved posts for manual publishing.
    """
    try:
        run_full = _import_run_full()  # robust import
    except ModuleNotFoundError:
        # Fallback: if the file isn't present in the container,
        # save a simple approved record so the UI can proceed.
        ap_id = str(uuid.uuid4())
        record = {
            "id": ap_id,
            "user_sub": user["sub"],
            "batch_id": None,
            "content": "Sample approved post from fallback pipeline.",
            "hashtags": ["Sample", "Portal"],
            "status": "APPROVED",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "li_post_id": None,
            "error_message": None,
        }
        DB["approved"][ap_id] = record
        return {"batch_id": None, "approved_count": 1, "approved_samples": [ap_id], "note": "Fallback sample created (test_complete_system not found in container)."}

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
            "status": "APPROVED",           # ready to publish
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
            rec["status"] = "PUBLISHED" if payload.publish_now else "LOCAL_DRAFT"
            rec["li_post_id"] = li_id
            rec["error_message"] = None

            DB["posts"][rec["id"]] = {
                "id": rec["id"],
                "user_sub": user["sub"],
                "target_type": target_type,
                "target_urn": target_urn,
                "commentary": commentary,
                "hashtags": hashtags,
                "lifecycle": "PUBLISHED" if payload.publish_now else "LOCAL_DRAFT",
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
