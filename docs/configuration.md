# 配置指南

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|:----:|--------|------|
| `AGNES_API_KEY` | 是 | — | Agnes AI 平台 API Key |
| `AGNES_BASE_URL` | 否 | `https://api.agnes-ai.cn/v1` | API 基础地址（国际版为 `https://apihub.agnes-ai.com/v1`） |
| `AGNES_IMAGE_MODEL` | 否 | `agnes-image-2.1-flash` | `agnes_image_generate` / `agnes_image_edit` 默认模型 |
| `AGNES_IMAGE_MODEL_V2` | 否 | `agnes-image-2.1-flash` | `agnes_image_generate_v2` 默认模型 |
| `AGNES_VIDEO_MODEL` | 否 | `agnes-video-v2.0` | 视频生成默认模型 |
| `AGNES_OUTPUT_DIR` | 否 | 源码树: `项目根/outputs`；安装后: `CWD/outputs` | 生成文件输出目录（建议使用绝对路径） |

变量可从两处读取（优先级：进程环境变量 > `.env` 文件）：

- **MCP 客户端配置**：在 `mcpServers` 的 `env` 字段中设置（推荐）
- **`.env` 文件**：本地开发模式下，服务启动时通过 `python-dotenv` 自动加载工作目录下的 `.env`

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

> 国内用户若无法访问 GitHub，可将 `git+https://github.com/Ryderey/agnes-mcp-studio` 替换为 `git+https://gitee.com/zzol_wow/agnes-mcp-studio`。

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

> 若客户端 MCP 连接超时较短，可先执行 `uv tool install --from git+<repo> agnes-media-mcp` 预装到本地，再将 `command` 指向 `~/.local/bin/agnes-media-mcp`（Windows：`%USERPROFILE%\.local\bin\agnes-media-mcp.exe`）的绝对路径，启动仅需约 2 秒。

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
| `mcp` | MCP 官方 SDK（使用其内置 FastMCP 实现工具注册与 stdio 运行） |
| `httpx` | HTTP 客户端 |
| `python-dotenv` | 环境变量加载 |

## 验证安装

```bash
# 检查模块导入
uv run python -c "from agnes_media_mcp.server import mcp; print('ok')"

# 运行单元测试
uv run python -m pytest tests/ -v

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

解决：确保 `AGNES_API_KEY` 已在 `.env` 或 MCP 客户端 `env` 中正确配置。

### 视频任务超时

`agnes_video_wait` / `agnes_video_generate` 返回超时错误时，响应中包含 `video_id` 和 `last_response`，可稍后使用 `agnes_video_status` 继续查询。

### 图像生成 400 错误

如果手动构造请求，注意 `response_format` 不可放在请求体顶层。本工具已自动将其放入 `extra_body` 内。

### 网络访问

确保运行环境可访问 `https://api.agnes-ai.cn`。视频生成结果可能托管在 `https://platform-outputs.agnes-ai.space`，下载时需确保该域名可达。企业代理环境需在 MCP 配置 `env` 中显式设置 `HTTPS_PROXY`。
