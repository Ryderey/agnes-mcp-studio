# 图像 API 文档

## 概述

Agnes Media MCP 提供两个图像生成工具和一个图像编辑工具，均通过 `POST /v1/images/generations` 端点调用。

| 工具 | 模型 | 适用场景 |
|------|------|----------|
| `agnes_image_generate` | `agnes-image-2.0-flash` | 通用文生图、图生图，精确像素尺寸 |
| `agnes_image_generate_v2` | `agnes-image-2.1-flash` | 高信息密度图像，分级尺寸 + 宽高比 |
| `agnes_image_edit` | `agnes-image-2.0-flash` | 图像编辑、风格迁移、多图合成 |

## agnes_image_generate

使用 `agnes-image-2.0-flash` 模型生成图像。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | — | 描述目标图像或编辑指令的文本提示 |
| `size` | string | 否 | `"1024x1024"` | 输出尺寸，如 `1024x768`、`1024x1024`、`768x1024` |
| `return_base64` | bool | 否 | `None` | 设为 `True` 时返回 Base64 数据而非 URL |
| `response_format` | string | 否 | `None` | 输出格式：`"url"` 或 `"b64_json"`（置于 extra_body 内发送） |
| `image_urls` | list[str] | 否 | `None` | 图生图输入图像（公开 URL 或 Data URI Base64） |
| `output_filename` | string | 否 | `None` | 自定义输出文件名 |
| `extra_body` | dict | 否 | `None` | 附加参数，透传至 API |

### 示例

```python
# 文生图
result = agnes.agnes_image_generate(
    prompt="产品摄影风格，玻璃立方体在白色背景上，柔和阴影",
    size="1024x768",
)

# 图生图
result = agnes.agnes_image_generate(
    prompt="将画面转换为赛博朋克风格，保留主体构图",
    size="1024x768",
    image_urls=["https://example.com/input.png"],
)

# 返回 Base64
result = agnes.agnes_image_generate(
    prompt="一只猫在窗台上",
    size="1024x1024",
    return_base64=True,
)
```

## agnes_image_generate_v2

使用 `agnes-image-2.1-flash` 模型，针对高信息密度、复杂构图和细节丰富的视觉场景优化。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | — | 文本提示 |
| `size` | string | 否 | `"1K"` | 分级尺寸：`1K`、`2K`、`3K`、`4K`（也接受精确尺寸如 `1024x768`） |
| `ratio` | string | 否 | `"1:1"` | 宽高比：`1:1`、`3:4`、`4:3`、`16:9`、`9:16`、`2:3`、`3:2`、`21:9` |
| `return_base64` | bool | 否 | `None` | 设为 `True` 时返回 Base64 |
| `response_format` | string | 否 | `None` | 输出格式（置于 extra_body 内发送） |
| `image_urls` | list[str] | 否 | `None` | 图生图输入图像 |
| `output_filename` | string | 否 | `None` | 自定义输出文件名 |
| `extra_body` | dict | 否 | `None` | 附加参数 |

### 输出尺寸参考

| 宽高比 | 1K | 2K | 3K | 4K |
|--------|----|----|----|----|
| `1:1` | 1024×1024 | 2048×2048 | 3072×3072 | 4096×4096 |
| `3:4` | 864×1152 | 1728×2304 | 2592×3456 | 3456×4608 |
| `4:3` | 1152×864 | 2304×1728 | 3456×2592 | 4608×3456 |
| `16:9` | 1312×736 | 2624×1472 | 3936×2208 | 5248×2944 |
| `9:16` | 736×1312 | 1472×2624 | 2208×3936 | 2944×5248 |
| `2:3` | 832×1248 | 1664×2496 | 2496×3744 | 3328×4992 |
| `3:2` | 1248×832 | 2496×1664 | 3744×2496 | 4992×3328 |
| `21:9` | 1568×672 | 3136×1344 | 4704×2016 | 6272×2688 |

### 示例

```python
# 16:9 壁纸级图像
result = agnes.agnes_image_generate_v2(
    prompt="浮空城市在峡谷之上，日出时分，电影写实风格",
    size="2K",
    ratio="16:9",
)

# 竖版海报
result = agnes.agnes_image_generate_v2(
    prompt="奇幻港口城市，悬崖上的建筑群，数百艘小船",
    size="3K",
    ratio="9:16",
)
```

## agnes_image_edit

通过 img2img 方式编辑或合成图像。

### 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `prompt` | string | 是 | — | 编辑指令 |
| `image_paths` | list[str] | 是 | — | 输入图像（公开 URL 或本地路径），多图启用合成模式 |
| `mask_path` | string | 否 | `None` | 不支持，传入会返回结构化错误 |
| `size` | string | 否 | `"1024x1024"` | 输出尺寸 |
| `ratio` | string | 否 | `None` | 宽高比（可选） |
| `return_base64` | bool | 否 | `None` | 返回 Base64 |
| `response_format` | string | 否 | `None` | 输出格式 |
| `output_filename` | string | 否 | `None` | 自定义输出文件名 |
| `extra_body` | dict | 否 | `None` | 附加参数 |

### 示例

```python
# 单图编辑
result = agnes.agnes_image_edit(
    prompt="将背景替换为未来城市夜景，保留人物面部和姿态",
    image_paths=["https://example.com/portrait.png"],
    size="1024x768",
)

# 多图合成
result = agnes.agnes_image_edit(
    prompt="将两个角色放入奇幻战斗场景中，动态光影",
    image_paths=[
        "https://example.com/character-1.png",
        "https://example.com/character-2.png",
    ],
    size="1024x768",
)
```

## 响应格式

所有图像工具返回统一结构：

```json
{
  "ok": true,
  "model": "agnes-image-2.0-flash",
  "image_urls": ["https://storage.googleapis.com/agnes-aigc/xxx.png"],
  "local_paths": ["/path/to/outputs/images/agnes-image-xxx.png"],
  "save_errors": [],
  "raw": { "created": 1780000000, "data": [...] }
}
```

| 字段 | 说明 |
|------|------|
| `ok` | 是否成功 |
| `model` | 使用的模型名 |
| `image_urls` | 远程图像 URL 列表 |
| `local_paths` | 已下载到本地的文件路径列表 |
| `save_errors` | 保存过程中的错误（如有） |
| `raw` | API 原始响应 |

## 重要约束

1. **`response_format` 禁止顶层放置**：必须放在 `extra_body` 内，否则 API 返回 400 错误。本工具已自动处理。
2. **不使用 `tags: ["img2img"]`**：图生图仅需通过 `extra_body.image` 传入图像数组。
3. **输入图像要求**：使用公开可访问的 HTTPS URL；无法公开时使用 Data URI Base64。
4. **超时建议**：图像生成可能需要数秒到数十秒，客户端超时建议 60s–360s。
