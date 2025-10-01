"""
LinkedIn OAuth with Local Server - Automatically captures the authorization code
Save as: linkedin_oauth_server.py
"""

import os
import json
import time
import threading
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"
PORT = 8000

# LinkedIn API version (required for all REST calls)
LINKEDIN_VERSION = os.getenv("LINKEDIN_VERSION", "202509")  # YYYYMM

# Optional: Company Page ID to publish as an Organization
LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID", "").strip()

# OIDC userinfo endpoint (works with scopes: openid profile email)
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Posts API endpoint (modern)
POSTS_URL = "https://api.linkedin.com/rest/posts"

authorization_code = None
server_running = False


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/callback":
            params = parse_qs(parsed_url.query)
            if "code" in params:
                authorization_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h1>✅ Authorization successful. You can close this window.</h1>".encode("utf-8"))
                print(f"\n✅ Authorization code received: {authorization_code[:30]}...")
            elif "error" in params:
                error = params.get("error", ["unknown"])[0]
                desc = params.get("error_description", ["No description"])[0]
                self.send_response(400)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h1>❌ Authorization failed</h1><p>{error} - {desc}</p>".encode("utf-8"))
                print(f"\n❌ Authorization error: {error} - {desc}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # silence default logs
        pass


class LinkedInOAuthServer:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redirect_uri = REDIRECT_URI
        self.server = None
        self.server_thread = None

    # -------- local server ----------
    def start_callback_server(self):
        global server_running
        print(f"\n🚀 Starting local server on port {PORT}...")
        self.server = HTTPServer(("localhost", PORT), OAuthCallbackHandler)
        server_running = True
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        print(f"✅ Server running at http://localhost:{PORT}")

    def stop_callback_server(self):
        global server_running
        if self.server:
            print("\n🛑 Stopping local server...")
            self.server.shutdown()
            server_running = False

    # -------- oauth flow ------------
    def get_authorization_url(self):
        # If you need org posting too, add w_organization_social to your app scopes
        scopes = "openid profile email w_member_social"
        extra = (os.getenv("EXTRA_SCOPES") or "").strip()
        if extra:
            scopes += f" {extra}"

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scopes,
            "state": "random_state_" + str(int(time.time()))
        }
        return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

    def authorize(self):
        global authorization_code
        print("\n" + "="*70)
        print("LINKEDIN OAUTH - AUTOMATIC FLOW")
        print("="*70)
        self.start_callback_server()
        auth_url = self.get_authorization_url()
        print("\n🔗 Authorization URL:\n", auth_url)
        time.sleep(1)
        webbrowser.open(auth_url)

        print("\n⏳ Waiting for authorization (timeout: 2 minutes)...")
        timeout = 120
        start = time.time()
        while authorization_code is None and (time.time() - start) < timeout:
            time.sleep(0.5)

        self.stop_callback_server()
        if authorization_code:
            print("\n✅ Authorization code captured successfully!")
            return self.exchange_code_for_token(authorization_code)
        print("\n❌ Timeout: No authorization code received")
        return None

    def exchange_code_for_token(self, code):
        print("\n🔄 Exchanging authorization code for access token...")
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        try:
            resp = requests.post(url, data=data, headers=headers, timeout=20)
            if resp.status_code == 200:
                tok = resp.json()
                access_token = tok.get("access_token")
                expires_in = tok.get("expires_in", 5184000)
                id_token = tok.get("id_token")
                print("\n" + "="*70)
                print("🎉 SUCCESS! ACCESS TOKEN OBTAINED!")
                print("="*70)
                print(f"Token: {access_token[:50]}...")
                print(f"Expires in: {expires_in // 86400} days")
                self.save_token(access_token, id_token=id_token)
                self.test_token(access_token, id_token=id_token)
                return access_token
            print(f"\n❌ Token exchange failed: {resp.status_code}\n{resp.text}")
            return None
        except Exception as e:
            print(f"\n❌ Error during token exchange: {e}")
            return None

    def save_token(self, token, id_token=None):
        os.makedirs("config", exist_ok=True)
        with open("config/linkedin_token.json", "w") as f:
            json.dump({"access_token": token, "id_token": id_token, "client_id": self.client_id, "timestamp": time.time()}, f, indent=2)
        print("\n✅ Token saved to: config/linkedin_token.json")

    def test_token(self, token, id_token=None):
        print("\n🔬 Testing access token via OIDC userinfo...")
        try:
            info = self.get_userinfo(token)
            sub = info.get("sub")
            if not sub:
                print("❌ Missing 'sub' in userinfo response.")
                return False
            author_urn = f"urn:li:person:{sub}"
            name = info.get("name") or f"{info.get('given_name','')} {info.get('family_name','')}".strip()
            print(f"\n✅ Token valid!")
            if name:
                print(f"👤 Name: {name}")
            print(f"🆔 Member sub: {sub}")
            print(f"🖊️ Author URN: {author_urn}")

            # PUBLISH a visible test post (not a UI draft)
            self.publish_member_test(token, author_urn)

            if LINKEDIN_ORG_ID:
                org_urn = f"urn:li:organization:{LINKEDIN_ORG_ID}"
                print(f"\n🏢 Also publishing a test post for {org_urn} ...")
                self.publish_org_test(token, org_urn)
            else:
                print("\nℹ️ Set LINKEDIN_ORG_ID in .env to also publish a Page test post.")
            return True
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            return False

    @staticmethod
    def get_userinfo(token: str):
        r = requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.status_code == 401:
            raise RuntimeError("401 from /v2/userinfo: token expired/invalid.")
        if r.status_code == 403:
            raise RuntimeError("403 from /v2/userinfo: missing OIDC scopes or access revoked.")
        if not r.ok:
            raise RuntimeError(f"/v2/userinfo failed: {r.status_code} {r.text}")
        return r.json()

    def _rest_headers(self, token: str):
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_VERSION
        }

    def publish_member_test(self, token: str, author_urn: str):
        print("\n📝 Publishing test post (member)...")
        payload = {
            "author": author_urn,
            "commentary": "🚀 API test post from my workflow (member).",
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED"},
            "lifecycleState": "PUBLISHED"
        }
        r = requests.post(POSTS_URL, headers=self._rest_headers(token), json=payload, timeout=20)
        if r.status_code in (201, 202):
            print("✅ Published to your feed.")
        else:
            print(f"⚠️ Could not publish member post: {r.status_code}\n{r.text}")

    def publish_org_test(self, token: str, org_urn: str):
        print("\n📝 Publishing test post (organization)...")
        payload = {
            "author": org_urn,
            "commentary": "🏢 API test post from my workflow (organization).",
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED"},
            "lifecycleState": "PUBLISHED"
        }
        r = requests.post(POSTS_URL, headers=self._rest_headers(token), json=payload, timeout=20)
        if r.status_code in (201, 202):
            print("✅ Published to the Page feed.")
        else:
            print(f"⚠️ Could not publish org post: {r.status_code}\n{r.text}")


def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   LinkedIn OAuth with Automatic Code Capture          ║
    ╚════════════════════════════════════════════════════════╝
    """)
    token_file = "config/linkedin_token.json"
    if os.path.exists(token_file):
        print("\n📂 Found existing token file")
        with open(token_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing_token = data.get("access_token")
        if existing_token:
            oauth = LinkedInOAuthServer()
            print("Testing existing token...")
            if oauth.test_token(existing_token, id_token=data.get("id_token")):
                print("\n✨ Token OK. Published test post(s).")
                return
            else:
                print("\n⚠️ Existing token invalid. Starting new auth...")

    oauth = LinkedInOAuthServer()
    token = oauth.authorize()
    if token:
        print("\n✅ Setup complete. Test post(s) published (member/Page).")
    else:
        print("\n❌ Authorization failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
