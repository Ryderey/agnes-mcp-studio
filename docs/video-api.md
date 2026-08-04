# 视频 API 文档

## 概述

Agnes Media MCP 提供异步视频生成能力，基于 `agnes-video-v2.0` 模型。工作流程为：提交任务 → 获取 `video_id` → 轮询状态 → 获取结果。

| 工具 | 说明 |
|------|------|
| `agnes_video_submit` | 提交视频任务，立即返回 `video_id` |
| `agnes_video_status` | 查询指定 `video_id` 的当前状态 |
| `agnes_video_wait` | 持续轮询直至完成/失败/超时 |
| `agnes_video_generate` | 提交 + 等待组合，一步到位 |

## API 端点

| 操作 | 端点 |
|------|------|
| 创建任务 | `POST https://api.agnes-ai.cn/v1/videos` |
| 查询结果（推荐） | `GET https://api.agnes-ai.cn/agnesapi?video_id=<VIDEO_ID>` |
| 查询结果（兼容） | `GET https://api.agnes-ai.cn/v1/videos/<TASK_ID>` |

本工具使用推荐的 `video_id` 端点。

## agnes_video_submit

提交视频生成任务，立即返回任务信息。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | — | 视频内容描述 |
| `duration` | float | 否 | `5.0` | 目标时长（秒），自动转换为 `num_frames` |
| `frame_rate` | int | 否 | `24` | 帧率（1–60）。官方类型为 number，MCP 收窄为 int |
| `resolution` | string | 否 | `"720p"` | 分辨率：`480p`、`720p`、`1080p` 或精确尺寸如 `1152x768` |
| `aspect_ratio` | string | 否 | `"16:9"` | 宽高比：`16:9`、`9:16`、`1:1`、`4:3`、`3:4` |
| `image` | string | 否 | `None` | 图生视频输入图像 URL |
| `mode` | string | 否 | `None` | 生成模式：`ti2vid`（图生视频）、`keyframes`（关键帧动画） |
| `negative_prompt` | string | 否 | `None` | 负面提示词，描述需要避免的内容 |
| `extra_body` | dict | 否 | `None` | 附加参数（如 `seed`、`num_inference_steps`） |

### num_frames 对齐规则

视频 API 要求 `num_frames` 满足：
- **≤ 441**（最大帧数限制）
- **符合 `8n + 1` 规则**（如 81、121、241、441）

本工具自动将 `duration × frame_rate` 对齐到最近的合法值。

| 目标时长 | 推荐参数 |
|----------|----------|
| 约 3 秒 | `num_frames: 81`, `frame_rate: 24` |
| 约 5 秒 | `num_frames: 121`, `frame_rate: 24` |
| 约 10 秒 | `num_frames: 241`, `frame_rate: 24` |
| 约 18 秒 | `num_frames: 441`, `frame_rate: 24` |

### 示例

```python
# 文生视频
result = agnes.agnes_video_submit(
    prompt="电影感镜头，猫在日落海滩上行走，柔和海浪",
    duration=5,
    resolution="720p",
    aspect_ratio="16:9",
)
print(result["video_id"])  # 用于后续查询

# 图生视频
result = agnes.agnes_video_submit(
    prompt="人物缓慢转身回望镜头，自然表情，电影运镜",
    image="https://example.com/portrait.png",
    duration=5,
)

# 关键帧动画
result = agnes.agnes_video_submit(
    prompt="在两个关键帧之间生成平滑过渡，保持视觉一致性",
    mode="keyframes",
    extra_body={
        "image": [
            "https://example.com/keyframe1.png",
            "https://example.com/keyframe2.png",
        ],
    },
)
```

> **实际发送的 HTTP 请求体（关键帧示例）：**
>
> ```json
> {
>   "model": "agnes-video-v2.0",
>   "prompt": "在两个关键帧之间生成平滑过渡，保持视觉一致性",
>   "num_frames": 121,
>   "frame_rate": 24,
>   "width": 1280,
>   "height": 720,
>   "extra_body": {
>     "mode": "keyframes",
>     "image": ["https://example.com/keyframe1.png", "https://example.com/keyframe2.png"]
>   }
> }
> ```
>
> 普通图生视频通过请求体顶层的 `image`（以及可选的顶层 `mode`）传图；关键帧动画才使用 `extra_body.image` 数组和 `extra_body.mode="keyframes"`。

### 响应

```json
{
  "ok": true,
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "status": "queued",
  "video_url": null,
  "raw": { ... }
}
```

## agnes_video_status

查询视频任务的当前状态。

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `video_id` | string | 是 | 提交任务时返回的 `video_id` |

### 任务状态

| 状态 | 说明 |
|------|------|
| `queued` | 任务在队列中等待 |
| `in_progress` | 视频正在生成 |
| `completed` | 视频生成成功 |
| `failed` | 视频生成失败 |

### 示例

```python
result = agnes.agnes_video_status("video_YOUR_VIDEO_ID")
print(result["status"])  # "queued" / "in_progress" / "completed" / "failed"
```

## agnes_video_wait

持续轮询任务状态直至完成、失败或超时。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `video_id` | string | 是 | — | 任务 `video_id` |
| `timeout_seconds` | float | 否 | `600.0` | 最大等待时间（秒） |
| `poll_interval_seconds` | float | 否 | `5.0` | 轮询间隔（秒） |
| `download` | bool | 否 | `True` | 完成后是否自动下载视频文件 |
| `output_filename` | string | 否 | `None` | 自定义输出文件名 |

轮询过程中遇到状态查询限流（429）或服务暂时不可用（503）时，工具会按 `poll_interval_seconds` 自动重试；其他查询错误会立即返回。

### 示例

```python
result = agnes.agnes_video_wait(
    "video_YOUR_VIDEO_ID",
    timeout_seconds=300,
    poll_interval_seconds=5,
)
if result["ok"]:
    print(result["local_path"])  # 本地视频文件路径
```

## agnes_video_generate

提交任务并等待完成的组合工具。

### 参数

包含 `agnes_video_submit` 的全部参数，加上：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `timeout_seconds` | float | 否 | `600.0` | 最大等待时间 |
| `poll_interval_seconds` | float | 否 | `5.0` | 轮询间隔 |
| `download` | bool | 否 | `True` | 是否自动下载 |
| `output_filename` | string | 否 | `None` | 自定义文件名 |

### 示例

```python
result = agnes.agnes_video_generate(
    prompt="宇航员在红色沙漠星球上行走，尘土飞扬，慢速跟踪镜头",
    duration=5,
    resolution="720p",
    aspect_ratio="16:9",
    negative_prompt="模糊, 低质量, 变形",
)

if result["ok"]:
    print(result["video_url"])   # 远程视频 URL
    print(result["local_path"])  # 本地文件路径
```

## 完成响应

任务完成时，视频 URL 通过 `metadata.url` 返回（官方文档推荐位置）。实测中也可能出现在顶层 `url` 字段（此时 `metadata` 为 `null`）。本工具对两种位置均能自动提取：

```json
{
  "ok": true,
  "task_id": "task_YOUR_TASK_ID",
  "video_id": "video_YOUR_VIDEO_ID",
  "status": "completed",
  "video_url": "https://platform-outputs.agnes-ai.space/videos/agnes-video-v2.0/video_xxx.mp4",
  "local_path": "/path/to/outputs/videos/agnes-media-xxx.mp4",
  "raw": {
    "status": "completed",
    "progress": 100,
    "seconds": "5.0",
    "size": "1152x768",
    "metadata": {
      "url": "https://platform-outputs.agnes-ai.space/videos/agnes-video-v2.0/video_xxx.mp4",
      "size_mapping": { "...": "..." }
    }
  }
}
```

## 推荐参数

| 场景 | 推荐设置 |
|------|----------|
| 标准视频 | `width: 1152`, `height: 768`, `num_frames: 121`, `frame_rate: 24` |
| 社交短视频 | `num_frames: 81` 或 `121`, `frame_rate: 24` |
| 更长视频 | 增大 `num_frames` 或降低 `frame_rate` |
| 更流畅运动 | `frame_rate: 24` 或 `30` |
| 可复现结果 | 设置固定 `seed`（通过 `extra_body`） |
| 关键帧过渡 | `mode: "keyframes"` + `extra_body.image` 数组 |
| 避免特定内容 | 使用 `negative_prompt` |

## 提示词最佳实践

### 文生视频

```
[主体] + [动作] + [场景] + [运镜] + [光线] + [风格]
```

示例：`年轻宇航员走过红色沙漠星球，尘土飞扬，慢速电影跟踪镜头，戏剧性日落光线，写实科幻风格`

### 图生视频

描述需要运动的部分和需要保持稳定的主体元素。

示例：`让人物产生微弱的呼吸动态，头发在风中轻轻飘动，背景灯光柔和闪烁，保持面部和服装一致`

### 关键帧动画

清晰描述关键帧之间的过渡关系。

示例：`从第一个关键帧平滑过渡到第二个关键帧，保持角色一致性、镜头角度连贯、场景间自然运动`

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 400 | 请求无效，检查参数 |
| 401 | 未授权，检查 API Key |
| 404 | 任务或视频未找到 |
| 500 | 服务器错误 |
| 503 | 服务繁忙，稍后重试 |
