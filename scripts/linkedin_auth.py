# scripts/linkedin_auth.py
"""One-time LinkedIn OAuth setup.

Prerequisites (do once at https://developer.linkedin.com/):
  1. Create an app (associate it with your LinkedIn profile or a company page).
  2. Under "Products", add "Share on LinkedIn" and
     "Sign In with LinkedIn using OpenID Connect".
  3. Under "Auth", add this exact redirect URL:  http://localhost:8914/callback
  4. Put the Client ID / Client Secret in .env as
     LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET.

Then run:  python scripts/linkedin_auth.py

A browser tab opens; approve access. The script saves LINKEDIN_ACCESS_TOKEN and
LINKEDIN_PERSON_URN into .env. Tokens last ~60 days; rerun this script to refresh.
"""
import logging
import os
import secrets
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

REDIRECT_URI = "http://localhost:8914/callback"
SCOPES = "openid profile w_member_social"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

result = {}
expected_state = secrets.token_urlsafe(16)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if params.get("state", [""])[0] != expected_state:
            result["error"] = "state mismatch - possible CSRF, try again"
        elif "code" in params:
            result["code"] = params["code"][0]
        else:
            result["error"] = params.get("error_description", ["unknown error"])[0]
        body = ("Authorization failed: " + result["error"]) if "error" in result \
            else "LinkedIn authorization complete. You can close this tab."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


def update_env_file(values):
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    for key, value in values.items():
        entry = f"{key}={value}"
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = entry
                break
        else:
            lines.append(entry)
    ENV_PATH.write_text("\n".join(lines) + "\n")


def main():
    load_dotenv(ENV_PATH)
    client_id = os.environ.get("LINKEDIN_CLIENT_ID")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit(
            "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env first "
            "(see the docstring at the top of this file)."
        )

    auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": expected_state,
    })

    server = HTTPServer(("localhost", 8914), CallbackHandler)
    logger.info("Opening browser for LinkedIn authorization...")
    webbrowser.open(auth_url)
    server.handle_request()  # blocks until LinkedIn redirects back
    server.server_close()

    if "error" in result:
        raise SystemExit(f"Authorization failed: {result['error']}")

    token_resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]

    userinfo = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    userinfo.raise_for_status()
    person_urn = f"urn:li:person:{userinfo.json()['sub']}"

    update_env_file({
        "LINKEDIN_ACCESS_TOKEN": access_token,
        "LINKEDIN_PERSON_URN": person_urn,
    })
    # access_token itself is never logged — only the non-secret profile URN.
    logger.info("Saved LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN (%s) to .env", person_urn)
    logger.info("The token expires in ~60 days; rerun this script to refresh it.")


if __name__ == "__main__":
    main()
