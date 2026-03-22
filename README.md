# 让 AI 接管你的飞书知识库
# Connect Your Feishu Wiki to AI via MCP

> 通过 MCP（Model Context Protocol）协议，让 Claude Code（或其他支持 MCP 的 AI 工具）直接读取、搜索你的飞书知识库。
>
> Connect Claude Code (or any MCP-compatible AI tool) to your Feishu wiki — search, read, and interact with your knowledge base without copy-pasting.

---

## 效果 / What you get

配置完成后，Claude Code 可以直接：

- 搜索飞书知识库中的文档 (`search-doc`)
- 读取文档完整内容 (`fetch-doc`)
- 列出知识库文档列表 (`list-docs`)

After setup, Claude Code can directly:
- Search your Feishu wiki (`search-doc`)
- Read full document content (`fetch-doc`)
- List documents in your wiki (`list-docs`)

---

## 前置准备 / Prerequisites

| 项目 | 说明 |
|------|------|
| 飞书账号 | 需要有知识库访问权限 |
| 飞书开放平台账号 | 用于创建自建应用，地址：https://open.feishu.cn/app |
| Python 3.10+ | 运行授权脚本 |
| Node.js 18+ | 运行 lark-mcp（npx 自动安装） |
| Claude Code | 配置 MCP 的 AI 工具，其他支持 MCP stdio 的工具同理 |

| Item | Notes |
|------|-------|
| Feishu account | With wiki access |
| Feishu Open Platform account | To create a self-built app: https://open.feishu.cn/app |
| Python 3.10+ | To run the auth script |
| Node.js 18+ | To run lark-mcp (auto-installed via npx) |
| Claude Code | MCP client; any stdio-compatible MCP client works |

---

## 第一步：创建飞书自建应用 / Step 1: Create a Feishu self-built app

1. 访问 [飞书开放平台](https://open.feishu.cn/app) → **创建企业自建应用**
2. 填写应用名称（如 `AI-Wiki-MCP`）、描述，上传图标
3. 进入应用 → **凭证与基础信息**，记录 `App ID` 和 `App Secret`

---

1. Go to [Feishu Open Platform](https://open.feishu.cn/app) → **Create self-built app**
2. Fill in app name (e.g. `AI-Wiki-MCP`), description, and icon
3. Go to app → **Credentials & Basic Info**, copy `App ID` and `App Secret`

---

## 第二步：申请 API 权限 / Step 2: Request API permissions

在应用管理页面 → **权限管理** → 搜索并添加以下权限：

In the app dashboard → **Permission Management** → search and add:

| 权限标识 / Permission | 说明 / Description |
|----------------------|-------------------|
| `wiki:wiki:readonly` | 查看知识库 / Read wiki |
| `docx:document:readonly` | 查看新版文档 / Read docs |
| `search:docs:read` | 搜索云文档 / Search docs |

> ⚠️ 权限申请后需要企业管理员审批（个人版飞书可直接生效）。
>
> ⚠️ Enterprise Feishu requires admin approval; personal Feishu takes effect immediately.

---

## 第三步：配置重定向 URL / Step 3: Configure redirect URL

在应用管理页面 → **安全设置** → **重定向 URL** → 添加：

In app dashboard → **Security Settings** → **Redirect URLs** → Add:

```
http://localhost:8080/callback
```

---

## 第四步：配置授权脚本 / Step 4: Configure the auth script

将本仓库克隆到本地：

Clone this repository:

```bash
git clone https://github.com/huasan2025/feishu-wiki-mcp.git
cd feishu-wiki-mcp
```

编辑 `feishu_auth.py`，填入你的 App ID 和 App Secret：

Edit `feishu_auth.py` and fill in your credentials:

```python
APP_ID = "cli_xxxxxxxxxxxxxxxxx"    # 替换为你的 App ID / Replace with your App ID
APP_SECRET = "xxxxxxxxxxxxxxxxx"    # 替换为你的 App Secret / Replace with your App Secret
```

---

## 第五步：首次授权 / Step 5: First-time authorization

```bash
python3 feishu_auth.py
```

脚本会：
1. 自动打开浏览器，跳转到飞书授权页
2. 你在飞书页面点击「允许授权」
3. 浏览器跳回 localhost，授权码自动被脚本捕获
4. 脚本换取 `access_token` 和 `refresh_token`，保存到 `tokens.json`

The script will:
1. Open your browser and navigate to Feishu's authorization page
2. Click "Allow" on the Feishu page
3. Browser redirects to localhost; the script captures the auth code automatically
4. Script exchanges code for `access_token` + `refresh_token`, saved to `tokens.json`

成功输出 / Success output:
```
Starting OAuth flow...
Opening browser for authorization...
Got authorization code: xxxxxxxxxx...
✅ Tokens saved to /path/to/tokens.json
   access_token: u-xxxxxxxxxxxxxxxxxx...
```

> `tokens.json` 已加入 `.gitignore`，不会被提交到 Git。
>
> `tokens.json` is in `.gitignore` and will not be committed to Git.

---

## 第六步：配置 Claude Code MCP / Step 6: Configure Claude Code MCP

给 `feishu_mcp_wrapper.sh` 添加执行权限：

Make the wrapper script executable:

```bash
chmod +x feishu_mcp_wrapper.sh
```

注册 MCP server（`--scope user` 表示对所有项目生效）：

Register the MCP server (`--scope user` applies to all projects):

```bash
claude mcp add feishu --scope user \
  -e LARK_APP_ID="cli_xxxxxxxxxxxxxxxxx" \
  -e LARK_APP_SECRET="xxxxxxxxxxxxxxxxx" \
  -- /absolute/path/to/feishu_mcp_wrapper.sh
```

> 将路径替换为你本地的实际绝对路径。
>
> Replace the path with the actual absolute path on your machine.

---

## 第七步：验证连接 / Step 7: Verify connection

```bash
claude mcp list
```

预期输出 / Expected output:
```
feishu: /path/to/feishu_mcp_wrapper.sh  - ✓ Connected
```

---

## Token 续期说明 / Token renewal

| Token | 有效期 / Validity | 续期方式 / Renewal |
|-------|-----------------|-------------------|
| `access_token` | 约 2 小时 / ~2 hours | 每次 MCP 启动时自动用 refresh_token 刷新 / Auto-refreshed on every MCP start |
| `refresh_token` | 约 30 天 / ~30 days | 手动重新运行 `python3 feishu_auth.py` / Re-run `feishu_auth.py` manually |

每次 Claude Code 启动并调用飞书 MCP 时，`feishu_mcp_wrapper.sh` 会先运行 `feishu_auth.py` 静默刷新 access_token，无需手动干预。

Every time Claude Code starts and calls the Feishu MCP, `feishu_mcp_wrapper.sh` runs `feishu_auth.py` to silently refresh the access token — no manual action needed.

30 天后 refresh_token 过期，重新运行一次：

After 30 days when refresh_token expires, simply re-run:

```bash
python3 feishu_auth.py
```

---

## 常见问题 / FAQ

**Q: 授权后 access_token 为空怎么办？**

检查 App ID 和 App Secret 是否正确，以及应用权限是否已审批通过。

**Q: MCP 连接失败怎么办？**

1. 确认 `tokens.json` 中 `access_token` 非空
2. 确认 Node.js 已安装（`node --version`）
3. 手动测试 wrapper：`bash feishu_mcp_wrapper.sh`

**Q: What if access_token is empty after authorization?**

Verify your App ID and App Secret are correct, and that the app permissions have been approved.

**Q: What if MCP connection fails?**

1. Confirm `access_token` in `tokens.json` is not empty
2. Confirm Node.js is installed (`node --version`)
3. Test the wrapper manually: `bash feishu_mcp_wrapper.sh`

---

## 文件说明 / File structure

```
.
├── README.md                # 本文档 / This document
├── feishu_auth.py           # OAuth 授权脚本 / OAuth authorization script
├── feishu_mcp_wrapper.sh    # MCP 启动包装脚本 / MCP startup wrapper
├── .gitignore               # 排除 tokens.json / Excludes tokens.json
└── tokens.json              # 运行后自动生成，勿提交 / Auto-generated, do not commit
```

---

## 相关链接 / Related links

- [飞书开放平台 / Feishu Open Platform](https://open.feishu.cn/app)
- [飞书知识库 API 概述 / Wiki API overview](https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview)
- [飞书 API 权限配置指南 / API permission guide](https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-qa#a40ad4ca)
- [lark-mcp npm 包 / lark-mcp npm package](https://www.npmjs.com/package/@larksuiteoapi/lark-mcp)
- [Model Context Protocol (MCP) 官网 / MCP official site](https://modelcontextprotocol.io)
- [Claude Code MCP 配置文档 / Claude Code MCP docs](https://docs.anthropic.com/en/docs/claude-code/mcp)

---

## License

MIT
