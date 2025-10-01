"""
LinkedIn Draft Publisher - Auto-prefer Organization posting when LINKEDIN_ORG_ID is set
Place this file in: src/infrastructure/social/linkedin_publisher.py
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import uuid
import requests

USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
POSTS_URL    = "https://api.linkedin.com/rest/posts"
API_VERSION  = os.getenv("LINKEDIN_VERSION", "202509")
ORG_ID_ENV   = (os.getenv("LINKEDIN_ORG_ID") or "").strip()


@dataclass
class LinkedInConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    access_token: Optional[str] = None
    organization_id: Optional[str] = ORG_ID_ENV or None
    person_urn: Optional[str] = None


@dataclass
class LinkedInDraft:
    content: str
    hashtags: List[str]
    visibility: str = "PUBLIC"
    draft_id: Optional[str] = None
    created_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None


class LinkedInPublisher:
    OAUTH_BASE_URL = "https://www.linkedin.com/oauth/v2"

    def __init__(self, config: LinkedInConfig, logger=None):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        if self.config.access_token:
            self._set_auth_headers(self.config.access_token)

    # ---------------- helpers ----------------
    def _set_auth_headers(self, token: str):
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": API_VERSION,
        })

    def _ensure_token(self):
        if not self.config.access_token:
            raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set. Authenticate first.")
        if "Authorization" not in self.session.headers:
            self._set_auth_headers(self.config.access_token)

    def _resolve_member_urn(self) -> str:
        self._ensure_token()
        if self.config.person_urn:
            return self.config.person_urn
        r = self.session.get(USERINFO_URL, timeout=20)
        if r.status_code == 401:
            raise RuntimeError("401 from /v2/userinfo: token expired/invalid.")
        if r.status_code == 403:
            raise RuntimeError("403 from /v2/userinfo: missing OIDC scopes (openid/profile/email) or access revoked.")
        if not r.ok:
            raise RuntimeError(f"/v2/userinfo failed: {r.status_code} {r.text}")
        sub = r.json().get("sub")
        if not sub:
            raise RuntimeError("userinfo missing 'sub'.")
        self.config.person_urn = f"urn:li:person:{sub}"
        if self.logger:
            self.logger.info(f"Resolved member URN: {self.config.person_urn}")
        return self.config.person_urn

    def _make_commentary(self, content: str, hashtags: Optional[List[str]]) -> str:
        content = (content or "").strip()
        if hashtags:
            block = " ".join(f"#{h.lstrip('#')}" for h in hashtags if h and str(h).strip())
            if block:
                return f"{content}\n\n{block}"
        return content

    # ---------------- oauth ------------------
    def get_authorization_url(self, state: str = None) -> str:
        """
        Build an OAuth URL. If we detect an Org ID, automatically request
        the Page scopes needed to publish as the organization.
        """
        scopes = ["openid", "profile", "email", "w_member_social"]
        # Auto-include org scopes if org posting is desired
        if self.config.organization_id:
            for s in ["rw_organization_admin", "w_organization_social"]:
                if s not in scopes:
                    scopes.append(s)
        # Allow additional scopes via env if caller wants
        extra = (os.getenv("EXTRA_SCOPES") or "").strip()
        if extra:
            for s in extra.split():
                if s not in scopes:
                    scopes.append(s)

        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(scopes),
        }
        if state:
            params["state"] = state
        from urllib.parse import urlencode
        return f"{self.OAUTH_BASE_URL}/authorization?{urlencode(params)}"

    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        url = f"{self.OAUTH_BASE_URL}/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret
        }
        r = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
        r.raise_for_status()
        tok = r.json()
        self.config.access_token = tok["access_token"]
        self._set_auth_headers(self.config.access_token)
        if self.logger:
            self.logger.info("Obtained LinkedIn access token")
        return tok

    async def get_profile_info(self) -> Dict[str, Any]:
        urn = self._resolve_member_urn()
        return {"id": urn.split(":")[-1], "urn": urn}

    # -------------- posting ------------------
    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = self.session.post(POSTS_URL, data=json.dumps(payload), timeout=30)
        if r.status_code in (201, 202):
            return r.json() if r.text else {"success": True}
        if r.status_code == 400:
            raise RuntimeError(f"400 Bad Request from /rest/posts: {r.text}")
        if r.status_code == 401:
            raise RuntimeError("401 Unauthorized: token invalid/expired for /rest/posts.")
        if r.status_code == 403:
            raise RuntimeError(
                "403 Forbidden from /rest/posts. Causes:\n"
                "- Missing scope w_member_social (member) or w_organization_social (org)\n"
                "- Missing rw_organization_admin (org discovery/permission)\n"
                "- Caller lacks required Page role (e.g., Content Admin)\n"
                "- App in Development mode and org/user not permitted\n"
                f"Details: {r.text}"
            )
        raise RuntimeError(f"{r.status_code} error from /rest/posts: {r.text}")

    async def create_draft_post(
        self,
        content: str,
        hashtags: List[str] = None,
        media_urls: List[str] = None,  # unused here; kept for signature
        publish_now: bool = True
    ) -> Dict[str, Any]:
        """
        If publish_now is True:
          - If LINKEDIN_ORG_ID is set -> publish to the Organization Page.
          - Else publish to the member profile.
        If publish_now is False: create a local draft (no LinkedIn call).
        """
        commentary = self._make_commentary(content, hashtags)

        if not publish_now:
            local_id = f"local-draft-{uuid.uuid4().hex[:12]}"
            draft = {
                "id": local_id,
                "state": "LOCAL_DRAFT",
                "commentary": commentary,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "target": "organization" if self.config.organization_id else "member"
            }
            if self.logger:
                self.logger.info(f"Stored local draft: {local_id}")
            return draft

        # prefer Organization if configured
        if self.config.organization_id:
            author_urn = f"urn:li:organization:{self.config.organization_id}"
        else:
            author_urn = self._resolve_member_urn()

        payload = {
            "author": author_urn,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED"},
            "lifecycleState": "PUBLISHED"
        }
        return self._post(payload)

    async def create_company_draft_post(
        self,
        content: str,
        hashtags: List[str] = None,
        organization_id: str = None,
        publish_now: bool = True
    ) -> Dict[str, Any]:
        """
        Explicit Company Page path (kept for callers that want to be explicit).
        """
        commentary = self._make_commentary(content, hashtags)

        if not publish_now:
            local_id = f"local-org-draft-{uuid.uuid4().hex[:12]}"
            draft = {
                "id": local_id,
                "state": "LOCAL_DRAFT",
                "commentary": commentary,
                "org_id": organization_id or self.config.organization_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            if self.logger:
                self.logger.info(f"Stored local org draft: {local_id}")
            return draft

        org_id = organization_id or self.config.organization_id
        if not org_id:
            raise ValueError("Organization ID required (LINKEDIN_ORG_ID or pass organization_id).")

        payload = {
            "author": f"urn:li:organization:{org_id}",
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED"},
            "lifecycleState": "PUBLISHED"
        }
        return self._post(payload)

    async def batch_create_drafts(self, posts: List[Dict[str, Any]], delay_seconds: int = 2) -> List[Dict[str, Any]]:
        results = []
        for i, post in enumerate(posts, 1):
            try:
                if self.logger:
                    self.logger.info(
                        f"Creating post {i}/{len(posts)} "
                        f"({'org' if self.config.organization_id else 'member'})"
                    )
                res = await self.create_draft_post(
                    content=post.get("content", ""),
                    hashtags=post.get("hashtags", []),
                    publish_now=True
                )
                results.append({"success": True, "post": post, "response": res})
                if i < len(posts):
                    await asyncio.sleep(delay_seconds)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to create post {i}: {e}")
                results.append({"success": False, "post": post, "error": str(e)})
        return results

    async def publish_approved_posts(self, approved_posts: List[Any]) -> Dict[str, Any]:
        self._ensure_token()
        results = {"total": len(approved_posts), "successful": 0, "failed": 0, "drafts": [], "errors": []}
        for post in approved_posts:
            try:
                content = getattr(post, "content", str(post))
                hashtags = getattr(post, "hashtags", []) or (getattr(post, "metadata", {}) or {}).get("hashtags", [])
                res = await self.create_draft_post(content=content, hashtags=hashtags, publish_now=True)
                results["successful"] += 1
                results["drafts"].append({
                    "post_id": getattr(post, "post_number", None),
                    "linkedin_id": (res.get("id") if isinstance(res, dict) else None),
                    "content_preview": content[:100] + "..." if len(content) > 100 else content
                })
                await asyncio.sleep(1)
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"post_id": getattr(post, "post_number", None), "error": str(e)})
                if self.logger:
                    self.logger.error(f"Failed to publish post: {e}")
        if self.logger:
            self.logger.info(f"Publishing complete: {results['successful']}/{results['total']} successful")
        return results


class LinkedInIntegrationService:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.publisher = LinkedInPublisher(self.config)

    def _load_config(self, config_path: str = None) -> LinkedInConfig:
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                return LinkedInConfig(**json.load(f))
        return LinkedInConfig(
            client_id=os.getenv("LINKEDIN_CLIENT_ID", ""),
            client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback"),
            access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", None),
            organization_id=os.getenv("LINKEDIN_ORG_ID", None),
        )

    async def setup_oauth(self) -> str:
        url = self.publisher.get_authorization_url()
        print(f"\nPlease visit this URL to authorize LinkedIn access:\n{url}\n")
        return url

    async def complete_oauth(self, authorization_code: str) -> bool:
        try:
            tok = await self.publisher.exchange_code_for_token(authorization_code)
            self._save_token(tok["access_token"])
            _ = await self.publisher.get_profile_info()
            print("Successfully connected to LinkedIn (OIDC).")
            # Friendly reminder if org is configured
            if self.config.organization_id:
                print("Org posting is enabled (LINKEDIN_ORG_ID detected). "
                      "Make sure your app scopes include rw_organization_admin w_organization_social, "
                      "and your user has a Page role (e.g., Content Admin).")
            return True
        except Exception as e:
            print(f"OAuth failed: {e}")
            return False

    def _save_token(self, access_token: str):
        os.environ["LINKEDIN_ACCESS_TOKEN"] = access_token
        os.makedirs("config", exist_ok=True)
        with open("config/linkedin_token.json", "w") as f:
            json.dump({"access_token": access_token}, f)

    async def publish_batch_results(self, batch) -> Dict[str, Any]:
        approved = batch.get_approved_posts()
        if not approved:
            return {"message": "No approved posts to publish"}
        target = "Organization Page" if self.config.organization_id else "member profile"
        print(f"\nPublishing {len(approved)} approved posts to LinkedIn ({target})...")
        return await self.publisher.publish_approved_posts(approved)


# Example integration
async def integrate_with_workflow(batch, linkedin_service: LinkedInIntegrationService):
    approved = batch.get_approved_posts()
    if not approved:
        print("No approved posts to publish")
        return
    target = "Organization Page" if linkedin_service.config.organization_id else "member profile"
    print(f"\nFound {len(approved)} approved posts")
    print(f"Publishing to LinkedIn ({target})...")
    results = await linkedin_service.publish_batch_results(batch)
    if results.get("drafts"):
        print("\n📝 Published posts:")
        for d in results["drafts"]:
            print(f"  - Post {d['post_id']}: {d['content_preview']}")
            print(f"    LinkedIn ID: {d['linkedin_id']}")
    if results.get("errors"):
        print("\n❌ Failed posts:")
        for e in results["errors"]:
            print(f"  - Post {e['post_id']}: {e['error']}")
    return results
