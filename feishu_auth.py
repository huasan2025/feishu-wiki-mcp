#!/usr/bin/env python3
"""
飞书 OAuth 授权脚本 / Feishu OAuth Authorization Script

用途：通过 OAuth 2.0 获取 user_access_token（UAT）和 refresh_token，
      保存到 tokens.json，供 MCP wrapper 使用。

Purpose: Obtain user_access_token (UAT) and refresh_token via OAuth 2.0,
         save to tokens.json for the MCP wrapper to consume.

使用前提 / Prerequisites:
  1. 已在飞书开放平台创建自建应用，并填入下方 APP_ID / APP_SECRET
     Created a self-built app on Feishu Open Platform with APP_ID / APP_SECRET filled in
  2. 已在应用「安全设置」→「重定向 URL」添加 http://localhost:8080/callback
     Added http://localhost:8080/callback to the app's redirect URL allowlist

用法 / Usage:
    python3 feishu_auth.py
"""

import http.server
import json
import os
import threading
import urllib.parse
import urllib.request
import webbrowser

# ── 配置（必填）/ Configuration (required) ─────────────────────────────────
APP_ID = "YOUR_APP_ID"        # 飞书应用 App ID / Feishu App ID
APP_SECRET = "YOUR_APP_SECRET"  # 飞书应用 App Secret / Feishu App Secret

REDIRECT_URI = "http://localhost:8080/callback"
TOKENS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens.json")
# ───────────────────────────────────────────────────────────────────────────


def build_auth_url() -> str:
    """构造飞书 OAuth 授权 URL / Build Feishu OAuth authorization URL"""
    params = urllib.parse.urlencode({
        "app_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "wiki:wiki:readonly docx:document:readonly search:docs:read",
        "state": "feishu_mcp",
    })
    return f"https://open.feishu.cn/open-apis/authen/v1/authorize?{params}"


def get_app_access_token() -> str:
    """
    获取应用级 access token（用于后续换取用户 token）
    Get app-level access token (used to exchange for user token)
    """
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"get_app_access_token failed: {data}")
    return data["app_access_token"]


def exchange_code_for_token(code: str) -> dict:
    """
    用授权码换取 user_access_token 和 refresh_token
    Exchange authorization code for user_access_token and refresh_token
    """
    app_token = get_app_access_token()
    url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
    payload = json.dumps({"grant_type": "authorization_code", "code": code}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {app_token}",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"exchange_code failed: {data}")
    return data.get("data", data)


def refresh_access_token(refresh_token: str) -> dict:
    """
    用 refresh_token 刷新 user_access_token（refresh_token 有效期约 30 天）
    Refresh user_access_token using refresh_token (valid for ~30 days)
    """
    app_token = get_app_access_token()
    url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
    payload = json.dumps({"grant_type": "refresh_token", "refresh_token": refresh_token}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {app_token}",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"refresh failed: {data}")
    return data.get("data", data)


def save_tokens(data: dict) -> dict:
    tokens = {
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
    }
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    uat = tokens.get("access_token") or ""
    print(f"✅ Tokens saved to {TOKENS_FILE}")
    if uat:
        print(f"   access_token: {uat[:20]}...")
    else:
        print("   ⚠️  access_token is empty — check API response")
    return tokens


def load_tokens() -> dict | None:
    if not os.path.exists(TOKENS_FILE):
        return None
    with open(TOKENS_FILE) as f:
        return json.load(f)


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """本地 HTTP 服务，用于接收飞书 OAuth 回调 / Local HTTP server for Feishu OAuth callback"""
    code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            CallbackHandler.code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>授权成功，可以关闭此页面 / Authorization successful, you may close this tab.</h2>".encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 屏蔽访问日志 / suppress access logs


def start_local_server():
    server = http.server.HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()
    server.server_close()


if __name__ == "__main__":
    if APP_ID == "YOUR_APP_ID" or APP_SECRET == "YOUR_APP_SECRET":
        print("❌ 请先在脚本中填入 APP_ID 和 APP_SECRET / Please fill in APP_ID and APP_SECRET first")
        exit(1)

    # 优先尝试用 refresh_token 静默刷新 / Try silent refresh with existing refresh_token
    existing = load_tokens()
    if existing and existing.get("refresh_token"):
        print("Found existing refresh_token, attempting silent refresh...")
        try:
            data = refresh_access_token(existing["refresh_token"])
            save_tokens(data)
            print("✅ Token refreshed silently.")
            exit(0)
        except Exception as e:
            print(f"Silent refresh failed ({e}), falling back to full OAuth flow...")

    # 完整 OAuth 流程 / Full OAuth flow
    print("Starting OAuth flow...")
    t = threading.Thread(target=start_local_server, daemon=True)
    t.start()

    auth_url = build_auth_url()
    print(f"Opening browser for authorization...")
    webbrowser.open(auth_url)
    print("Waiting for callback (timeout: 120s)...")

    t.join(timeout=120)

    if not CallbackHandler.code:
        print("❌ Timed out. Make sure the browser opened and you completed authorization.")
        exit(1)

    print(f"Got authorization code: {CallbackHandler.code[:10]}...")
    data = exchange_code_for_token(CallbackHandler.code)
    save_tokens(data)
