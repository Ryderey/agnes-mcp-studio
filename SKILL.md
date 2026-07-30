---
name: agnes-media-generation
description: Use when the user explicitly mentions "agnes" (case-insensitive) AND requests image generation, image editing, video generation, or image-to-video animation
---

# Agnes Media Generation

## Overview

MCP-based media generation skill providing text-to-image, image-to-image, and text/image-to-video capabilities through Agnes AI models (`agnes-image-2.0-flash`, `agnes-image-2.1-flash`, `agnes-video-v2.0`).

## When to Use

**Gate condition (MANDATORY):** User message MUST contain the keyword `agnes` (case-insensitive: Agnes, AGNES, agnes all match). Without this keyword, do NOT activate this skill even if the request involves image/video generation.

Trigger examples:
- "使用 agnes 生成一张赛博朋克城市图片"
- "用 Agnes 帮我做一个产品宣传视频"
- "agnes 画一张水彩风格的猫"
- "AGNES generate a 4K wallpaper of mountains"

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

Choose the appropriate tool based on the task:

| Task | Tool | Key Parameters |
|------|------|----------------|
| Standard image generation | `agnes_image_generate` | `size`: exact pixels like `1024x768` |
| High-detail / high-resolution image | `agnes_image_generate_v2` | `size`: `1K`–`4K`, `ratio`: aspect ratio |
| Image editing / style transfer | `agnes_image_edit` | `image_paths`: source images |
| Multi-image composition | `agnes_image_edit` | `image_paths`: multiple images |
| Video generation (simple) | `agnes_video_generate` | All-in-one: submit + wait |
| Video generation (async control) | `agnes_video_submit` then `agnes_video_wait` | Two-step with manual polling |

### Decision Rules

1. **Default image generation**: Use `agnes_image_generate` with `size="1024x1024"`.
2. **User requests high resolution, wallpaper, poster, or detailed scene**: Use `agnes_image_generate_v2` with appropriate `size` tier (`2K`, `3K`, `4K`) and `ratio`.
3. **User provides reference images for editing**: Use `agnes_image_edit`.
4. **Video under 10 seconds**: Use `agnes_video_generate` directly.
5. **Video requiring progress feedback**: Use `agnes_video_submit`, report `video_id`, then call `agnes_video_wait`.

## Image Prompt Construction

Build prompts using this structure for best results:

```
[Subject] + [Scene / Background] + [Style] + [Lighting] + [Composition] + [Quality]
```

Example:
```
A professional product photo of wireless headphones on a clean white background,
soft studio lighting, sharp details, commercial photography style
```

For image editing prompts, specify what to change AND what to preserve:
```
Change the background to a futuristic city at night while keeping the person's
face, outfit, and pose unchanged
```

## Video Prompt Construction

Build video prompts using:

```
[Subject] + [Action] + [Scene] + [Camera Movement] + [Lighting] + [Style]
```

Example:
```
A young astronaut walking across a red desert planet, dust blowing in the wind,
slow cinematic tracking shot, dramatic sunset lighting, realistic sci-fi style
```

## Video Workflow

Video generation is asynchronous. Follow this workflow:

1. Call `agnes_video_generate` (or `agnes_video_submit` + `agnes_video_wait`)
2. Inform the user that video generation typically takes 30 seconds to several minutes
3. On success, present the `local_path` (downloaded file) and/or `video_url`
4. On timeout, report the `video_id` so the user can check status later with `agnes_video_status`

### Video Duration Guidelines

| Duration | Setting |
|----------|---------|
| ~3 seconds | `duration=3` |
| ~5 seconds | `duration=5` (default) |
| ~10 seconds | `duration=10` |
| ~18 seconds (max) | `duration=18` |

The tool automatically aligns frame count to the required `8n+1` rule. Maximum is ~18 seconds at 24fps.

## Size Reference for agnes_image_generate_v2

| Ratio | 1K | 2K | 4K |
|-------|----|----|-----|
| `1:1` | 1024×1024 | 2048×2048 | 4096×4096 |
| `16:9` | 1312×736 | 2624×1472 | 5248×2944 |
| `9:16` | 736×1312 | 1472×2624 | 2944×5248 |
| `4:3` | 1152×864 | 2304×1728 | 4608×3456 |
| `3:4` | 864×1152 | 1728×2304 | 3456×4608 |

## Constraints

- Do NOT place `response_format` at the top level of any request; the tool handles this internally via `extra_body`.
- Do NOT pass `tags: ["img2img"]`; image-to-image uses `image_urls` parameter directly.
- Video `num_frames` is auto-aligned; do not manually calculate frame counts.
- Input images must be publicly accessible HTTPS URLs or local file paths (auto-converted to Data URI Base64).
- `mask_path` is not supported; do not attempt to use it.
- Video results may take 30s–5min depending on duration and server load.

## Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| `missing_api_key` | `AGNES_API_KEY` not set | Ask user to configure their API key |
| `invalid_prompt` | Empty prompt | Ask user for a description |
| `http_error` (400) | Invalid parameters | Check size/ratio values against reference |
| `http_error` (401) | Invalid API key | Ask user to verify their key |
| `timeout` | Video task timed out | Report `video_id` for later status check |
| `task_failed` | Video generation failed | Report error details, suggest retrying with simpler prompt |

## Output Handling

- Images are saved to `outputs/images/` automatically. Present the `local_paths` to the user.
- Videos are saved to `outputs/videos/` when `download=True` (default). Present the `local_path`.
- Always show generated images to the user using Markdown image syntax when possible.
- For videos, provide the file path and/or remote URL.
