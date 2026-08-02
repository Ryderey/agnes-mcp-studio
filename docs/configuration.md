# 配置指南

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `AGNES_API_KEY` | 是 | — | Agnes AI 平台 API Key |
| `AGNES_BASE_URL` | 否 | `https://api.agnes-ai.cn/v1` | API 基础地址 |
| `AGNES_IMAGE_MODEL` | 否 | `agnes-image-2.1-flash` | 图像生成默认模型 |
| `AGNES_IMAGE_MODEL_V2` | 否 | `agnes-image-2.1-flash` | 图像生成 v2 默认模型 |
| `AGNES_VIDEO_MODEL` | 否 | `agnes-video-v2.0` | 视频生成默认模型 |
| `AGNES_OUTPUT_DIR` | 否 | 源码树: `项目根/outputs`；安装后: `CWD/outputs` | 生成文件输出目录（建议使用绝对路径） |

## 获取 API Key

1. 登录 [Agnes AI 控制台](https://www.agnes-ai.cn)
2. 进入 API Key 管理页面
3. 创建并复制 API Key

> **安全提示**：API Key 为敏感信息，请勿在公开代码仓库、前端代码、截图或公开文档中暴露。

> **国内 / 国际平台不互通**：`agnes-ai.cn` 与 `agnes-ai.com` 的账号和 API Key 完全独立，不可混用。修改 `AGNES_BASE_URL` 切换端点时，必须同时更换为对应平台签发的 Key。

## 本地开发配置

复制示例环境文件：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
AGNES_API_KEY=sk-your-real-key-here
AGNES_BASE_URL=https://api.agnes-ai.cn/v1
AGNES_IMAGE_MODEL=agnes-image-2.1-flash
AGNES_IMAGE_MODEL_V2=agnes-image-2.1-flash
AGNES_VIDEO_MODEL=agnes-video-v2.0
AGNES_OUTPUT_DIR=./outputs
```

服务启动时通过 `python-dotenv` 自动加载 `.env` 文件。

## MCP 客户端集成配置

### 通用 JSON 格式（Claude Desktop / Cursor / Qoder 等）

```json
{
  "mcpServers": {
    "agnes_media": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Ryderey/agnes-mcp-studio",
        "agnes-media-mcp"
      ],
      "env": {
        "AGNES_API_KEY": "sk-your-real-key-here",
        "AGNES_OUTPUT_DIR": "/absolute/path/to/outputs"
      }
    }
  }
}
```

### Hermes 配置（YAML）

在 Hermes 配置文件中添加 MCP 服务器：

```yaml
mcp_servers:
  agnes_media:
    command: "uvx"
    args:
      - "--from"
      - "git+https://github.com/Ryderey/agnes-mcp-studio"
      - "agnes-media-mcp"
    env:
      AGNES_API_KEY: "sk-your-real-key-here"
      AGNES_BASE_URL: "https://api.agnes-ai.cn/v1"
      AGNES_IMAGE_MODEL: "agnes-image-2.1-flash"
      AGNES_IMAGE_MODEL_V2: "agnes-image-2.1-flash"
      AGNES_VIDEO_MODEL: "agnes-video-v2.0"
      AGNES_OUTPUT_DIR: "/absolute/path/to/outputs"
    timeout: 600
    connect_timeout: 60
    tools:
      include:
        - agnes_image_generate
        - agnes_image_generate_v2
        - agnes_image_edit
        - agnes_video_submit
        - agnes_video_status
        - agnes_video_wait
        - agnes_video_generate
      prompts: false
      resources: false
```

### 配置说明

| 字段 | 说明 |
|------|------|
| `command` | `uvx`（uv 自带的包运行器，跨平台可用） |
| `args` | `--from git+<repo>` 指定源，`agnes-media-mcp` 为控制台入口名 |
| `env` | 环境变量（API Key 在此配置） |
| `timeout` | 工具调用超时（秒），视频生成建议 600 |
| `connect_timeout` | 连接超时（秒） |
| `tools.include` | 启用的工具白名单 |

## 输出目录结构

生成的文件按类型存放在输出目录下：

```
outputs/
├── images/          # 图像生成结果
│   ├── agnes-image-1720000000-a1b2c3d4.png
│   └── agnes-image-1720000001-e5f6g7h8-1.png
└── videos/          # 视频生成结果
    └── agnes-media-1720000002-i9j0k1l2.mp4
```

文件名格式：`{前缀}-{时间戳}-{随机ID}[-{序号}].{扩展名}`

可通过 `output_filename` 参数自定义文件名。

## CC-Switch 集成配置（Claude CLI）

CC-Switch 是 Claude CLI 的模型代理工具，可将 Claude CLI 请求路由到 Agnes AI API。

下载地址：https://github.com/farion1231/cc-switch/releases

### 前置条件

- 已安装 Claude CLI
- 已安装 CC-Switch（基于 v3.16.1）
- 有效的 Agnes AI API Key

### 配置步骤

1. **启动 CC-Switch**，在顶部工具栏选择 `Claude CLI`

2. **添加 Provider**：点击右上角加号，选择 `Claude Provider` → `Custom Provider`

3. **填写配置**：

| 字段 | 值 |
|------|----|
| API Key | 你的 Agnes API Key（无需加 `Bearer` 前缀） |
| Request URL | `https://api.agnes-ai.cn/v1` |
| API Format | `OpenAI Chat Completions` |
| Auth Field | 默认（或 `ANTHROPIC_AUTH_TOKEN`） |

4. **获取模型列表**：点击「Fetch Model List」验证连通性

5. **模型映射**（推荐）：

```
Sonnet  -> agnes-2.0-flash
Opus    -> agnes-2.0-flash
Haiku   -> agnes-2.0-flash
```

6. **自定义参数**（兼容性配置）：

```json
{
  "allowed_openai_params": ["thinking", "context_management"],
  "litellm_settings": {
    "drop_params": true
  }
}
```

7. **保存配置**，然后启用路由：
   - 进入设置 → `Route` → 启用 `Local Route`
   - 开启 Claude 路由开关

8. **启用 Agnes Provider**：在 Provider 列表中找到 Agnes 配置项，点击「Enable」

### 验证

打开 Claude CLI，执行一次对话或编码任务。如果配置正确，将返回 Agnes 模型的响应。

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 无法获取模型列表 | 检查 URL 是否为 `https://api.agnes-ai.cn/v1`，API Key 是否有效 |
| 认证失败 | API Key 无需手动加 `Bearer` 前缀 |
| 请求参数不兼容 | 确认已添加 `drop_params: true` 配置 |
| 未使用 Agnes 模型 | 检查 Local Route 和 Claude 路由开关是否已启用 |

## WorkBuddy 集成配置

WorkBuddy 支持通过自定义模型接入 Agnes 文本模型，并可通过 Skills 调用图像和视频模型。

### 前置条件

- 已安装 WorkBuddy（基于 v4.24.5）
- 有效的 Agnes AI API Key

### 文本模型配置

1. 打开 WorkBuddy，点击页面上的 `Auto`，选择「Configure Custom Model」

2. 在 Provider 列表底部选择 `Other` 或 `Custom`

3. 点击「Add Model」，填写：

| 字段 | 值 |
|------|----|
| Provider | `Custom` |
| API Base URL | `https://api.agnes-ai.cn/v1` |
| API Key | 你的 Agnes API Key |
| Model Name | `agnes-2.0-flash` |

4. 点击「Save」保存

5. 在聊天界面选择 `agnes-2.0-flash` 模型

### 图像和视频模型（通过 Skills）

在 WorkBuddy 中输入以下提示，让其自动创建 Skill：

```
我想使用 Agnes Image 2.0 模型来生成图像和视频。
请访问其 API 平台 https://agnes-ai.com/doc/overview 并将其打包为 Skill。
```

创建成功后即可通过 Skill 调用图像/视频生成能力。

### 验证

发送一条普通聊天消息（如「你好，请介绍一下自己」），如果返回 Agnes 模型的响应则配置成功。

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 文本模型无响应 | 检查 API Base URL 和 API Key 是否正确 |
| 模型列表无 agnes-2.0-flash | 确认模型名拼写正确（区分大小写） |
| Skill 创建失败 | 确保 WorkBuddy 可访问文档 URL，且当前模型支持读取文档 |
| 视频任务耗时长 | 视频生成为异步任务，需等待完成后查看结果 |

## 安装依赖

### 方式一：uvx 直接运行（无需 clone）

```bash
uvx --from git+https://github.com/Ryderey/agnes-mcp-studio agnes-media-mcp
```

### 方式二：本地开发

```bash
git clone https://github.com/Ryderey/agnes-mcp-studio
cd agnes-mcp-studio
uv sync
```

主要依赖：

| 包 | 用途 |
|----|------|
| `fastmcp` | MCP 服务器框架 |
| `httpx` | HTTP 客户端 |
| `python-dotenv` | 环境变量加载 |

## 验证安装

```bash
# 检查模块导入
uv run python -c "from agnes_media_mcp.server import mcp; print('ok')"

# 运行单元测试
uv run python -m pytest tests/ -v

# 检查 MCP 工具注册
uv run fastmcp list src/agnes_media_mcp/server.py --json

# Hermes 侧验证
hermes mcp list
hermes mcp test agnes_media
```

## 常见问题

### API Key 未配置

调用任何工具时返回：

```json
{
  "ok": false,
  "error": {
    "code": "missing_api_key",
    "message": "Set AGNES_API_KEY in the environment before calling Agnes."
  }
}
```

解决：确保 `AGNES_API_KEY` 已在 `.env` 或 Hermes env 中正确配置。

### 视频任务超时

`agnes_video_wait` / `agnes_video_generate` 返回超时错误时，响应中包含 `video_id` 和 `last_response`，可稍后使用 `agnes_video_status` 继续查询。

### 图像生成 400 错误

如果手动构造请求，注意 `response_format` 不可放在请求体顶层。本工具已自动将其放入 `extra_body` 内。

### 网络访问

确保运行环境可访问 `https://api.agnes-ai.cn`。视频生成结果可能托管在 `https://platform-outputs.agnes-ai.space`，下载时需确保该域名可达。
