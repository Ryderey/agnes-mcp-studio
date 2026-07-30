---
name: agnes-media-generation
description: Use when the user explicitly mentions "agnes" (case-insensitive) AND requests image generation, image editing, video generation, or image-to-video animation
---

# Agnes Media Generation

## Overview

MCP-based media generation skill providing text-to-image, image-to-image, image editing, text/image-to-video, and keyframe animation through Agnes AI models.

**Models:** `agnes-image-2.0-flash` · `agnes-image-2.1-flash` · `agnes-video-v2.0`

**Prerequisite:** The `agnes_media` MCP server must be configured and running. If tools are unavailable, ask the user to check their MCP configuration.

## When to Use

**Gate condition (MANDATORY):** User message MUST contain the keyword `agnes` (case-insensitive: Agnes, AGNES, agnes all match). Without this keyword, do NOT activate this skill even if the request involves image/video generation.

Trigger examples:
- "使用 agnes 生成一张赛博朋克城市图片"
- "用 Agnes 帮我做一个产品宣传视频"
- "agnes 画一张水彩风格的猫"
- "AGNES generate a 4K wallpaper of mountains"
- "用agnes把这张图变成动漫风格"（无空格也匹配）

After the gate passes, match intent:
- Generate, create, or draw an image
- Edit, transform, or restyle an existing image
- Combine or compose multiple images into one
- Generate or create a video
- Animate an image or create a video from an image

## When NOT to Use

- User requests image/video generation WITHOUT mentioning "agnes" (use other tools/skills instead)
- User asks about image/video understanding or analysis (this is generation, not understanding)
- User asks for text generation, chat, or code (use text models instead)
- User asks to search the web for existing images
- User needs real-time video streaming or live video processing

## Tool Selection

| Task | Tool | Key Parameters |
|------|------|----------------|
| Standard image (text-to-image / img2img) | `agnes_image_generate` | `size`: exact pixels `1024x768`; `image_urls`: reference images |
| High-resolution image (wallpaper/poster) | `agnes_image_generate_v2` | `size`: `1K`–`4K`; `ratio`: aspect ratio; `image_urls`: optional |
| Image editing / style transfer | `agnes_image_edit` | `image_paths`: source images (URL or local path) |
| Multi-image composition | `agnes_image_edit` | `image_paths`: multiple images |
| Text-to-video (simple) | `agnes_video_generate` | All-in-one: submit + wait |
| Image-to-video / animation | `agnes_video_generate` | `image`: source image URL; `mode`: `"ti2vid"` |
| Video (async with progress) | `agnes_video_submit` → `agnes_video_wait` | Two-step with manual polling |

### Decision Rules

1. **Default image generation** (no special requirements): Use `agnes_image_generate` with `size="1024x1024"`.
2. **User requests high resolution, wallpaper, poster, 4K, or detailed scene**: Use `agnes_image_generate_v2` with appropriate `size` tier and `ratio`. Default to `size="2K"`, `ratio="16:9"` for wallpapers.
3. **User provides reference images for editing/compositing**: Use `agnes_image_edit` with `image_paths`.
4. **User provides a reference image but wants a NEW image in similar style**: Use `agnes_image_generate` or `_v2` with `image_urls`.
5. **Video ≤ 18 seconds (all cases)**: Use `agnes_video_generate` directly.
6. **Video requiring progress feedback or very long timeout**: Use `agnes_video_submit`, report `video_id` to user, then call `agnes_video_wait`.
7. **Animate a still image**: Use `agnes_video_generate` with `image=<url>` and `mode="ti2vid"`.

## Prompt Construction

### Image Prompts

Structure: `[Subject] + [Scene/Background] + [Style] + [Lighting] + [Composition] + [Quality]`

```
A professional product photo of wireless headphones on a clean white background,
soft studio lighting, sharp details, commercial photography style
```

For image editing, specify what to change AND what to preserve:
```
Change the background to a futuristic city at night while keeping the person's
face, outfit, and pose unchanged
```

### Video Prompts

Structure: `[Subject] + [Action] + [Scene] + [Camera Movement] + [Lighting] + [Style]`

```
A young astronaut walking across a red desert planet, dust blowing in the wind,
slow cinematic tracking shot, dramatic sunset lighting, realistic sci-fi style
```

### Prompt Tips

- Chinese prompts work well; no need to translate to English.
- Use `negative_prompt` (video tools) to exclude unwanted elements, e.g. `"blurry, low quality, watermark"`.
- Be specific about camera movement for video: "slow dolly in", "tracking shot", "static camera".

## Video Workflow

Video generation is asynchronous. Follow this workflow:

1. Call `agnes_video_generate` (or `agnes_video_submit` + `agnes_video_wait`)
2. Inform the user that video generation typically takes 30 seconds to several minutes
3. On success: present the `local_path` (downloaded file) and/or `video_url`
4. On timeout: report the `video_id` so the user can check status later with `agnes_video_status`

### Video Duration & Resolution

| Duration | Setting | Notes |
|----------|---------|-------|
| ~3 seconds | `duration=3` | Quick preview |
| ~5 seconds | `duration=5` | Default |
| ~10 seconds | `duration=10` | Standard clip |
| ~18 seconds | `duration=18` | Maximum |

Resolution options: `"480p"`, `"720p"` (default), `"1080p"`.
Aspect ratios: `"16:9"` (default), `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"`.

Frame count is auto-aligned to the `8n+1` rule (max 441 frames at 24fps).

## Size Reference for agnes_image_generate_v2

| Ratio | 1K | 2K | 3K | 4K |
|-------|----|----|----|-----|
| `1:1` | 1024×1024 | 2048×2048 | 3072×3072 | 4096×4096 |
| `16:9` | 1312×736 | 2624×1472 | 3936×2208 | 5248×2944 |
| `9:16` | 736×1312 | 1472×2624 | 2208×3936 | 2944×5248 |
| `4:3` | 1152×864 | 2304×1728 | 3456×2592 | 4608×3456 |
| `3:4` | 864×1152 | 1728×2304 | 2592×3456 | 3456×4608 |
| `3:2` | 1248×832 | 2496×1664 | 3744×2496 | 4992×3328 |
| `2:3` | 832×1248 | 1664×2496 | 2496×3744 | 3328×4992 |
| `21:9` | 1344×576 | 2688×1152 | 4032×1728 | 5376×2304 |

## Constraints

- Input images must be publicly accessible HTTPS URLs or local file paths (local files are auto-converted to Base64 Data URI).
- `mask_path` is not supported; if user asks for inpainting with mask, explain it's unavailable.
- Video results may take 30s–5min depending on duration and server load.
- The tool handles `response_format`, `extra_body`, and `num_frames` alignment internally — do not pass these manually.

## Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| `missing_api_key` | `AGNES_API_KEY` not set | Ask user to configure their API key in MCP settings |
| `invalid_prompt` | Empty prompt | Ask user for a description |
| `unsupported_parameter` | Used `mask_path` | Explain mask/inpainting is not supported |
| `http_error` (400) | Invalid parameters | Check size/ratio values against reference table |
| `http_error` (401) | Invalid API key | Ask user to verify their key |
| `http_error` (429) | Rate limited | Wait a moment and retry |
| `timeout` | Video task timed out | Report `video_id` for later status check |
| `task_failed` | Video generation failed | Report error details, suggest retrying with simpler prompt |

## Output Handling

- Images are saved to `outputs/images/` automatically. Present the `local_paths` to the user.
- Videos are saved to `outputs/videos/` when `download=True` (default). Present the `local_path`.
- **Always show generated images inline** using Markdown:
  ```
  ![generated image](/absolute/path/to/output.png)
  ```
- For videos, provide the file path and/or remote URL:
  ```
  视频已生成：`/path/to/outputs/videos/agnes-media-xxx.mp4`
  远程链接：https://...
  ```
- If multiple images are returned, show all of them.
