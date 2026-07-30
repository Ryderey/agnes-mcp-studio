# Agnes Media MCP

基于 FastMCP 的 Agnes 图像与视频生成 MCP 服务器（国内版）。

本服务通过环境变量读取凭据，请勿将真实 API Key 放入版本控制文件。

## 工作流程

完整流程图见 [docs/workflow.drawio](docs/workflow.drawio)（在 GitHub 上点击即可查看，或用 [draw.io](https://app.diagrams.net) 打开编辑）。

**流程概览：**

```
用户请求 ─→ [② 包含 "agnes"?] ─否─→ 不激活，交给其他工具
                    │是
                    ▼
         ③ 意图匹配 (Skill: When to Use)
                    │
                    ▼
         ④ 决策规则 → 选择工具
          ├─ 标准图像 → agnes_image_generate
          ├─ 高分辨率 → agnes_image_generate_v2 (1K-4K + ratio)
          ├─ 图像编辑 → agnes_image_edit
          └─ 视频     → agnes_video_generate / submit+wait
                    │
                    ▼
         ⑤ 构造 Prompt (Skill 指南)
                    │
                    ▼
         ⑥ MCP Server 处理 (payload / Base64 / 8n+1)
                    │
                    ▼
         ⑦ Agnes API (api.agnes-ai.cn/v1)
          ├─ 图像: 同步返回 b64_json / url
          └─ 视频: video_id → 轮询 GET /agnesapi
                    │
                    ▼
         ⑧ 保存文件 → outputs/images/ | outputs/videos/
                    │
                    ▼
         ⑨ Agent 展示结果 (Markdown / 路径 / URL)
                    │
                    ▼
         ⑩ 用户获得媒体文件
```

> **Skill 层**（②③④⑤⑨）负责触发判断、工具选择、Prompt 构造和结果展示；**MCP 层**（⑥⑧）负责协议适配；**API 层**（⑦）负责实际推理。

## 工具列表

| 工具名 | 说明 |
|--------|------|
| `agnes_image_generate` | 文生图 / 图生图（`agnes-image-2.0-flash`），精确像素尺寸 |
| `agnes_image_generate_v2` | 高信息密度图像生成（`agnes-image-2.1-flash`），分级尺寸 `1K`–`4K` + 宽高比 |
| `agnes_image_edit` | 图像编辑 / 多图合成，通过 `extra_body.image` 传入参考图 |
| `agnes_video_submit` | 提交视频生成任务（`POST /videos`），返回 `video_id` |
| `agnes_video_status` | 查询视频任务状态（`GET /agnesapi?video_id=<VIDEO_ID>`） |
| `agnes_video_wait` | 轮询任务直至完成、失败或超时 |
| `agnes_video_generate` | 提交视频任务并等待完成（submit + wait 组合） |

## 快速开始

<!-- TODO: 发布前全局替换 "你的用户名" 为实际 GitHub 用户名/组织名 -->

### 方式一：uvx 直接运行（推荐，无需 clone）

只需安装 [uv](https://docs.astral.sh/uv/)，即可一行启动：

```bash
uvx --from git+https://github.com/你的用户名/agnes-media-mcp agnes-media-mcp
```

### 方式二：本地开发

```bash
git clone https://github.com/你的用户名/agnes-media-mcp
cd agnes-media-mcp
uv sync
uv run agnes-media-mcp
```

### 配置环境变量

复制 `.env.example` 为 `.env` 进行本地测试：

```bash
AGNES_API_KEY=your_agnes_api_key_here
AGNES_BASE_URL=https://api.agnes-ai.cn/v1
AGNES_IMAGE_MODEL=agnes-image-2.0-flash
AGNES_IMAGE_MODEL_V2=agnes-image-2.1-flash
AGNES_VIDEO_MODEL=agnes-video-v2.0
AGNES_OUTPUT_DIR=./outputs
```

`AGNES_API_KEY` 为必填项，其余均有默认值。

### MCP 客户端配置（通用 JSON 格式）

适用于 Claude Desktop、Cursor、Qoder 等支持 MCP 的客户端：

```json
{
  "mcpServers": {
    "agnes_media": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/你的用户名/agnes-media-mcp",
        "agnes-media-mcp"
      ],
      "env": {
        "AGNES_API_KEY": "your_agnes_api_key_here"
      }
    }
  }
}
```

### Hermes 配置（YAML）

```yaml
mcp_servers:
  agnes_media:
    command: "uvx"
    args:
      - "--from"
      - "git+https://github.com/你的用户名/agnes-media-mcp"
      - "agnes-media-mcp"
    env:
      AGNES_API_KEY: "your_agnes_api_key_here"
      AGNES_BASE_URL: "https://api.agnes-ai.cn/v1"
      AGNES_IMAGE_MODEL: "agnes-image-2.0-flash"
      AGNES_IMAGE_MODEL_V2: "agnes-image-2.1-flash"
      AGNES_VIDEO_MODEL: "agnes-video-v2.0"
      AGNES_OUTPUT_DIR: "./outputs"
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

## 验证

```bash
uv run python -c "from agnes_media_mcp.server import mcp; print('import ok')"
uv run python -m pytest tests/ -v
uv run fastmcp inspect src/agnes_media_mcp/server.py:mcp
uv run fastmcp list src/agnes_media_mcp/server.py --json
```

Hermes 侧检查：

```bash
hermes config edit
hermes mcp list
hermes mcp test agnes_media
```

## 使用示例

### 图像生成（2.0 Flash）

```python
from agnes_media_mcp.server import agnes_image_generate

result = agnes_image_generate(
    prompt="一只陶瓷咖啡杯放在钢制桌面上，柔和光线",
    size="1024x1024",
)
```

### 图像生成（2.1 Flash，分级尺寸）

```python
from agnes_media_mcp.server import agnes_image_generate_v2

result = agnes_image_generate_v2(
    prompt="赛博朋克城市夜景，霓虹灯反射，电影质感",
    size="2K",
    ratio="16:9",
)
```

### 视频生成

```python
from agnes_media_mcp.server import agnes_video_generate

result = agnes_video_generate(
    prompt="缓慢推进镜头，玻璃雕塑在画廊中旋转",
    duration=5,
    resolution="720p",
    aspect_ratio="16:9",
)
```

> `agnes_video_wait` 和 `agnes_video_generate` 可能运行数分钟，测试时建议使用较短超时。

## 文档

详细 API 文档请参阅 `docs/` 目录：

- [图像 API 文档](docs/image-api.md)
- [视频 API 文档](docs/video-api.md)
- [配置指南](docs/configuration.md)

## 注意事项

- Base URL 使用国内端点：`https://api.agnes-ai.cn/v1`
- `response_format` 必须放在 `extra_body` 内，不可置于请求体顶层
- 图生图不使用 `tags: ["img2img"]`，参考图通过 `extra_body.image` 传入
- `agnes_image_generate_v2` 使用 `agnes-image-2.1-flash`，支持 `1K`–`4K` 分级尺寸 + `ratio` 宽高比
- 视频 `num_frames` 自动对齐 `8n+1` 规则（上限 441）
- 视频状态轮询使用 `video_id`，端点为 `GET /agnesapi?video_id=<VIDEO_ID>`
- 视频结果 URL 从响应的 `metadata.url` 字段提取
- `mask_path` 参数会返回结构化不支持错误（当前文档未描述 mask 功能）
- 超时响应包含 `video_id` 和 `last_response`，可稍后继续轮询
