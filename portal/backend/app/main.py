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
# Ensure repo root is on PYTHONPATH so `src/` is importable even if run from portal/backend
# --------------------------------------------------------------------------------------
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]  # .../Content-Validation-System
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# --------------------------------------------------------------------------------------
# Load your LinkedIn integration service from the repo
# --------------------------------------------------------------------------------------
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService

# --------------------------------------------------------------------------------------
# Environment / Config
# --------------------------------------------------------------------------------------
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", "http://localhost:3000")   # Next.js
PORTAL_API_BASE = os.getenv("PORTAL_API_BASE", "http://localhost:8001")   # FastAPI self
REDIRECT_URI     = os.getenv("LINKEDIN_REDIRECT_URI", f"{PORTAL_API_BASE}/auth/linkedin/callback")

LINKEDIN_CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LI_VERSION             = os.getenv("LINKEDIN_VERSION", "202509")

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
app = FastAPI(title="Content Portal API", version="0.2.0")

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
        "message": "Content Portal API – use /auth/linkedin/login or the UI at http://localhost:3000",
    }

@app.get("/healthz")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/debug/oauth")
def debug_oauth():
    return {
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "scopes": scopes_for_auth(want_org_scopes())
    }

# --------------------------------------------------------------------------------------
# OAuth: login + callback
# --------------------------------------------------------------------------------------
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
        "org_preferred": os.getenv("LINKEDIN_ORG_ID")
    }

@app.get("/api/orgs")
def list_orgs(user=Depends(get_user)):
    token = DB["tokens"][user["sub"]]["access_token"]
    headers = rest_headers(token)
    headers["X-RestLi-Method"] = "FINDER"
    params = {
        "q": "roleAssignee",
        "role": "ADMINISTRATOR",
        "state": "APPROVED",
        "assignee": f"urn:li:person:{user['sub']}"
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
# Compose / Publish (immediate or draft)
# --------------------------------------------------------------------------------------
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
                # fallback for older signature (always draft)
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
    """
    Runs your generation/validation pipeline and stores approved posts for manual publishing.
    """
    from tests.test_complete_system import test_complete_system as run_full

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
