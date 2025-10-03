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
from fastapi.responses import RedirectResponse, JSONResponse, PlainTextResponse
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
# LinkedIn service
# --------------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# --------------------------------------------------------------------------------------
# Helpers: env handling and URL normalization
# --------------------------------------------------------------------------------------
def _env(name: str, default: str = "") -> str:
    """Read env, strip whitespace/newlines and surrounding quotes."""
    raw = os.getenv(name, default)
    if raw is None:
        return default
    # strip whitespace and any accidental surrounding quotes
    val = raw.strip().strip('"').strip("'")
    return val

def _normalize_base(url: str) -> str:
    """Normalize a base URL: strip, drop trailing slash, ensure scheme present."""
    url = (url or "").strip()
    # remove accidental newlines in middle
    url = url.replace("\r", "").replace("\n", "")
    if url.endswith("/"):
        url = url[:-1]
    return url

def _join_url(base: str, path: str) -> str:
    """Join base + path without creating double slashes."""
    base = _normalize_base(base)
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"

def _build_redirect_uri() -> str:
    """
    If LINKEDIN_REDIRECT_URI is set, use it (sanitized). Otherwise build from PORTAL_API_BASE.
    NEVER add a trailing slash unless explicitly present in the env override.
    """
    explicit = _env("LINKEDIN_REDIRECT_URI", "")
    if explicit:
        # sanitize but do not alter path semantics
        uri = explicit.replace("\r", "").replace("\n", "").strip()
        return uri
    # default from API base
    base = _normalize_base(_env("PORTAL_API_BASE", "http://localhost:8001"))
    return _join_url(base, "/auth/linkedin/callback")

# --------------------------------------------------------------------------------------
# Environment / Config (sanitized)
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = _normalize_base(_env("PORTAL_BASE_URL", "http://localhost:3000"))   # Next.js
PORTAL_API_BASE = _normalize_base(_env("PORTAL_API_BASE", "http://localhost:8001"))   # FastAPI (this app)
REDIRECT_URI    = _build_redirect_uri()

LINKEDIN_CLIENT_ID     = _env("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = _env("LINKEDIN_CLIENT_SECRET", "")
LI_VERSION             = _env("LINKEDIN_VERSION", "202509")

AUTH_URL  = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO  = "https://api.linkedin.com/v2/userinfo"
POSTS_URL = "https://api.linkedin.com/rest/posts"
ORGS_URL  = "https://api.linkedin.com/rest/organizationAcls"  # X-RestLi-Method: FINDER

# --------------------------------------------------------------------------------------
# Instantiate integration service (reads env + token file if your code supports it)
# --------------------------------------------------------------------------------------
svc = LinkedInIntegrationService()

# --------------------------------------------------------------------------------------
# In-memory DB (simple for MVP). We can persist to file/DB later.
# --------------------------------------------------------------------------------------
DB: Dict[str, Dict[str, Any]] = {
    "users": {},     # key = li_sub -> {sub, name, email}
    "tokens": {},    # key = li_sub -> {access_token, version, updated_at}
    "posts": {},     # key = internal id -> posts ledger (already sent to LI as draft/live)
    "approved": {}   # key = internal id -> approved by pipeline, not yet sent to LI
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
# Middleware: collapse double slashes in path (//auth/...) -> (/auth/...)
# --------------------------------------------------------------------------------------
@app.middleware("http")
async def collapse_double_slashes(request: Request, call_next):
    path = request.url.path
    if "//" in path:
        # collapse and redirect (preserve query)
        collapsed = "/".join([seg for seg in path.split("/") if seg != ""])
        collapsed = "/" + collapsed
        if collapsed != path:
            target = str(request.url.replace(path=collapsed))
            return RedirectResponse(target, status_code=307)
    return await call_next(request)

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def want_org_scopes() -> bool:
    """Ask for org scopes if an org is configured or EXTRA_SCOPES is set."""
    return bool(_env("LINKEDIN_ORG_ID") or _env("EXTRA_SCOPES"))

def scopes_for_auth(include_org: bool) -> str:
    scopes = ["openid", "profile", "email", "w_member_social"]
    if include_org:
        for s in ["rw_organization_admin", "w_organization_social"]:
            if s not in scopes:
                scopes.append(s)
    extra = (_env("EXTRA_SCOPES") or "").split()
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

def get_user(request: Request) -> Dict[str, Any]:
    sub = request.cookies.get("li_sub")
    if not sub:
        raise HTTPException(401, "Not authenticated")
    user = DB["users"].get(sub)
    if not user:
        raise HTTPException(401, "User not found")
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

# ---- Robust importer for test_complete_system (Option B) ------------------------------
def _import_run_full():
    """
    Robustly import the coroutine `test_complete_system` regardless of location.
    Tries root file, alt name, tests package, src/tests, then direct file path.
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
    publish_now: bool = True  # if False, create local draft (no LinkedIn call)

class PublishApprovedIn(BaseModel):
    ids: List[str]
    target: str = "AUTO"            # AUTO | MEMBER | ORG
    org_id: Optional[str] = None
    publish_now: bool = False       # False = create DRAFTs (local drafts, by design)

# --------------------------------------------------------------------------------------
# Basic routes
# --------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "ok": True,
        "message": "Content Portal API – use /auth/linkedin/login or the UI at PORTAL_BASE_URL",
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "scopes_default_with_org": scopes_for_auth(True),
        "scopes_default_member_only": scopes_for_auth(False),
        "portal_base_url": PORTAL_BASE_URL,
        "api_base": PORTAL_API_BASE,
    }

# --------------------------------------------------------------------------------------
# OAuth: login + callback
# --------------------------------------------------------------------------------------
@app.get("/auth/linkedin/login")
def linkedin_login(include_org: bool = True):
    # IMPORTANT: pass the exact REDIRECT_URI computed above
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scopes_for_auth(include_org and want_org_scopes()),
        "state": str(int(time.time()))
    }
    return RedirectResponse(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

# Optional: HEAD support so `curl -I` shows a redirect instead of 405
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
def linkedin_callback(code: str, state: Optional[str] = None):
    # Exchange code for access token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,  # must match exactly what was used in /login and in LinkedIn App
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
        # Make mismatches obvious
        return JSONResponse(
            status_code=tok.status_code,
            content={
                "error": "Token exchange failed",
                "tip": "Ensure LinkedIn App Redirect URL EXACTLY matches `redirect_uri` below.",
                "redirect_uri_we_sent": REDIRECT_URI,
                "linkedin_response": tok.text
            }
        )

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
    DB["tokens"][sub] = {
        "access_token": access_token,
        "version": LI_VERSION,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    # Expose token to service + persist to file used by CLI/tests
    set_token_for_service(access_token)

    # Set a readable cookie for the FE session (demo scope)
    resp = RedirectResponse(url=_join_url(PORTAL_BASE_URL, "/dashboard"))
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
        "org_preferred": _env("LINKEDIN_ORG_ID") or None
    }

@app.get("/api/orgs")
def list_orgs(user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    headers = rest_headers(token)
    headers["X-RestLi-Method"] = "FINDER"
    # Many accounts accept assignee; some sandbox configs reject it.
    # Try with assignee first; fall back without it.
    params_with = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}"
    }
    r = requests.get(ORGS_URL, headers=headers, params=params_with, timeout=20)
    if r.status_code == 400 and "QUERY_PARAM_NOT_ALLOWED" in r.text:
        params_no = {
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "state": "APPROVED",
        }
        r = requests.get(ORGS_URL, headers=headers, params=params_no, timeout=20)
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
# Compose / Publish (immediate OR local draft)
# --------------------------------------------------------------------------------------
@app.post("/api/posts")
async def create_post(payload: ComposeIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    default_org = _env("LINKEDIN_ORG_ID") or None
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
                # fallback for older signature
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
# Run pipeline: store approved (no auto publish)
# --------------------------------------------------------------------------------------
@app.post("/api/run-batch")
async def run_batch(user=Depends(get_user), publish: bool = False):
    """
    Runs your generation/validation pipeline and stores approved posts for manual publishing.
    """
    run_full = _import_run_full()  # robustly import the coroutine

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

@app.post("/api/approved/publish")
async def publish_approved(payload: PublishApprovedIn, user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    set_token_for_service(token)

    results = []
    default_org = _env("LINKEDIN_ORG_ID") or None

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
